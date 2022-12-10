from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
import os
import discord
from discord.ext import commands, tasks
from string import Formatter
from datetime import timedelta

# bot 사용하기 위한 token
token = ""

# discord channel id
ID = 1029174448512843787

# message 읽고 쓸 수 있는 권한을 줍니다.
intents = discord.Intents.default()
intents.message_content = True

# command를 "/이름"으로 실행
bot = commands.Bot(command_prefix='/', intents=intents)

class TodoList:
    SchoolID = os.environ.get('School_ID')  # SchoolID = '' put your eclass id
    SchoolPW = os.environ.get('School_PW')  # SchoolPW = '' put your eclass pw
    # 제목, 과목, 시간, 가장 최근에 알림을 보낸 시간
    def __init__(self, title, subject, datetime, reminder):
        self.title = title
        self.subject = subject
        self.datetime = datetime
        self.reminder = reminder

# timedelta 값을 주어진 format으로 출력해주는 함수
def timeformat(timedelta, fmt):
    seconds = int(timedelta.total_seconds())
    formatter = Formatter()
    requirement = [requires[1] for requires in formatter.parse(fmt)]
    fields = ('D', 'H', 'M', 'S')
    utime = {'D': 24 * 60 * 60, 'H': 60 * 60, 'M': 60, 'S': 1}
    values = {}
    for field in fields:
        if field in requirement and field in utime:
            values[field], seconds = divmod(seconds, utime[field])
    return formatter.format(fmt, **values)

# eclass todolist crawling
def crawling():
    # driver option
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument("no-sandbox")

    # Chrome browser만 지원합니다. 컴퓨터에 설치된 Chrome 버전에 맞는 driver를 설치해주세요.
    driver = webdriver.Chrome('./chromedriver.exe', options=options)
    driver.get('https://eclass.seoultech.ac.kr/ilos/main/member/login_form.acl')
    driver.implicitly_wait(3)

    # 로그인
    driver.find_element(By.ID, 'usr_id').send_keys(TodoList.SchoolID)
    driver.find_element(By.ID, 'usr_pwd').send_keys(TodoList.SchoolPW)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btntype')))
    driver.find_element(By.CLASS_NAME, 'btntype').click()

    # TodoList html 파일 얻기
    script = 'return $.ajax({ url: \"https://eclass.seoultech.ac.kr/ilos/mp/todo_list.acl\", type: \"POST\", ' \
             'async: false, data: { todoKjList: \'\', chk_cate: \'ALL\', encoding: \"utf-8\" }, success: function(data) ' \
             '{ return data; } }).responseText;'
    result = driver.execute_script(script=script)
    soup = bs(result, 'html.parser')
    driver.close()

    # 원하는 정보만 list에 저장(제목, 과목, 마감 날짜)
    todo_titles = soup.find_all('div', {'class': 'todo_title'})
    titles = []
    for todo_title in todo_titles:
        titles.append(todo_title.text.strip())

    todo_subjects = soup.find_all('div', {'class': 'todo_subjt'})
    subjects = []
    for todo_subject in todo_subjects:
        subjects.append(todo_subject.text.strip())
    todo_dates = soup.find_all('span', {'class': 'todo_date'})

    # string을 datetime으로 바꾸어 저장
    dates = []
    datetime_format = "%Y.%m.%d %p %I:%M"
    for todo_date in todo_dates:
        todo_date = todo_date.text.replace('/', '').replace('~', '').strip()
        if len(todo_date) > 23:
            todo_date = todo_date[:22]
        todo_date.strip()
        todo_date = todo_date.replace("(월)", '').replace("(화)", '').replace("(수)", '').replace("(목)", '')
        todo_date = todo_date.replace("(금)", '').replace("(토)", '').replace("(일)", '')
        todo_date = todo_date.replace('오전', 'AM').replace('오후', 'PM')
        todo_date = datetime.strptime(todo_date, datetime_format)
        dates.append(todo_date)
    return titles, subjects, dates

@tasks.loop(seconds=10)
async def remindbot(todolists, numbers, starts, cycles):
    channel = bot.get_channel(ID)
    for i, (number, start, cycle) in enumerate(zip(numbers, starts, cycles)):
        # todolist을 전부 받아와 특정 번호만 todolist에 저장
        todolist = todolists[number - 1]

        # 비교 위해 timedelta로 형변환
        start = timedelta(days=start)
        cycle = timedelta(minutes=cycle)

        # 마감 날짜에서 현재 시간을 빼준다.
        diff = todolist.datetime - datetime.now()
        # reminder에 timedelta(0)이 아니라면 -> 알림을 보내 준 적이 있으면
        if todolist.reminder != timedelta(0):
            diff2 = datetime.now() - todolist.reminder
            # 가장 최근에 알림을 보내준 시간으로 부터 cycle분만큼이 더 지났을 때 and 마감기한이 지나지 않았을 때
            if diff2 > cycle and diff > timedelta(0):
                todolist.reminder = datetime.now()
                await channel.send(f'{todolist.subject} {todolist.title}이(가)')
                await channel.send(timeformat(diff, '{D}days {H}hours {M:02}minutes 남았습니다.'))
            else:
                pass
        # 알림을 보내 준 적이 없다면
        else:
            # 기한이 지나지 않았고 diff가 start보다 작을 때 -> 마감기한에서 현재시간이 start일 보다 적게 남았을 때
            if timedelta(0) < diff < start:
                todolist.reminder = datetime.now()
                await channel.send(f'{todolist.subject} {todolist.title}이(가)')
                await channel.send(timeformat(diff, '{D}days {H}hours {M:02}minutes 남았습니다.'))
            else:
                pass

@bot.command(name="활성화")
async def _activate(ctx):
    channel = bot.get_channel(ID)
    await ctx.send('활성화되었습니다.(TodoList가 전부 뜰 때까지 기다려주세요...)')
    titles, subjects, dates = crawling()
    reminder = timedelta(0)
    TodoLists = []
    # 존재하는 항목 Todolist list에 저장 항목번호 possible_nums에 저장
    possible_nums = set()
    possible_days = set([i for i in range(1, 101)])
    possible_mins = set([i for i in range(1, 61)])
    for i, (title, subject, date) in enumerate(zip(titles, subjects, dates)):
        todolist = TodoList(title, subject, date, reminder)
        await channel.send(f'{i + 1}: {title} {subject} {date}')
        TodoLists.append(todolist)
        possible_nums.add(i + 1)

    def strtolist(num):
        num1 = str(num.content)
        num1 = list(map(int, num1.split()))
        return num1

    def listtoset(num):
        num1 = strtolist(num)
        num2 = set()
        for n in num1:
            num2.add(int(n))
        return num2

    # issubset 함수를 쓰기 위해 set으로 바꾸어 줌
    # 각각 possible이라는 set에 있는 원소이어야 다음 단계로 넘어감
    def iscontent(num):
        num2 = listtoset(num)
        return num.channel == channel and num2.issubset(possible_nums)
    def isday(num):
        num2 = listtoset(num)
        return num.channel == channel and num2.issubset(possible_days)
    def ismin(num):
        num2 = listtoset(num)
        return num.channel == channel and num2.issubset(possible_mins)

    # 사용자한테 몇 일 전부터 몇 분마다 알림을 보내줄지 입력 받기
    await channel.send('항목을 골라주세요.(중복 선택 가능) ex)1 2 3 / 4 7(공백으로 숫자 구분)')
    nums = await bot.wait_for("message", check=iscontent, timeout=30)
    nums = strtolist(nums)
    await channel.send(f'{len(nums)}개씩 입력해 주세요!!!')
    await channel.send('몇 일 전부터 알림을 보내드릴까요??')
    days = await bot.wait_for("message", check=isday, timeout=30)
    days = strtolist(days)
    await channel.send('몇 분마다 알림을 보내드릴까요??')
    minutes = await bot.wait_for("message", check=ismin, timeout=30)
    minutes = strtolist(minutes)

    # 알림 시작
    remindbot.start(TodoLists, nums, days, minutes)

    @bot.command(name="재설정")
    @commands.has_permissions(administrator=True) # 반복 가능하도록 True로 설정해줌
    async def _deactivate(ctx):
        await ctx.send('재설정.')
        remindbot.cancel() # 기존에 알림 보내주던 것 멈추기
        channel = bot.get_channel(ID)

        # reminder에 있던 시간 초기화
        for number in nums:
            todolist = TodoLists[number - 1]
            todolist.reminder = timedelta(0)

        #101 추가 102 삭제 103 변경
        sets = set([101, 102, 103])
        def check(num):
            num2 = listtoset(num)
            return num.channel == channel and num2.issubset(sets)

        await channel.send('항목을 골라주세요. 101 추가 102 삭제 103 변경(위 todolist 참고)')

        # 기존에 설정되있는 값 출력
        for y, (nu, da, min) in enumerate(zip(nums, days, minutes)):
            todo = TodoLists[nu - 1]
            await channel.send(f'{y + 1}번: {todo.subject} {todo.title}이(가) {da}일 전부터 {min}분마다 알림')

        # 추가 삭제 변경(list 이용)
        num = await bot.wait_for("message", check=check, timeout=30)
        num = int(num.content)
        if num == 101:
            await channel.send('항목 번호(추가)를 알려주세요.')
            n = await bot.wait_for("message", check=iscontent, timeout=30)
            n = int(n.content)
            nums.append(n)
            await channel.send('몇 일 전부터(추가) 알림을 보내드릴까요?')
            d = await bot.wait_for("message", check=isday, timeout=30)
            d = int(d.content)
            days.append(d)
            await channel.send('몇 분마다(추가) 알림을 보내드릴까요?')
            m = await bot.wait_for("message", check=ismin, timeout=30)
            m = int(m.content)
            minutes.append(m)
        elif num == 102:
            await channel.send('항목 번호(삭제)를 알려주세요.')
            n = await bot.wait_for("message", check=iscontent, timeout=30)
            n = int(n.content)
            del nums[n - 1]
            del days[n - 1]
            del minutes[n - 1]
        elif num == 103:
            await channel.send('항목 번호(변경)를 알려주세요.')
            n = await bot.wait_for("message", check=iscontent, timeout=30)
            n = int(n.content)
            index = nums.index(n)
            await channel.send('몇 일 전부터(변경) 알림을 보내드릴까요?')
            d = await bot.wait_for("message", check=isday, timeout=30)
            d = int(d.content)
            days[index] = d
            await channel.send('몇 분마다(변경) 알림을 보내드릴까요?')
            m = await bot.wait_for("message", check=ismin, timeout=30)
            m = int(m.content)
            minutes[index] = m
        # 재시작
        remindbot.start(TodoLists, nums, days, minutes)
bot.run(token)

