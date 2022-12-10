# TodoList-Reminder
Eclass **TodoList**를 discord로 **알림** 보내주기
## Contents
1. [Outline](#Outline)
2. [Description](#Description)
3. [Example](#Example)
4. [Conclusion](#Conclusion)
## Outline
코로나가 유행하기 시작한 이후로 대학생들은 온라인 수업을 받게 되면서 eclass가 활성화 되었습니다. 대면 수업이 활성화된 지금도  공지사항을 확인하거나 과제를 제출할 때 eclass를 활용합니다. 저의 경우, 제출하지 않은 과제에 대한 알림이 하루 전에만 떠서 과제를 놓친 적이 있었습니다. eclass가 사용자가 설정한대로 알림을 보내주면 좋을 것 같아 만들게 되었습니다. 
## Description
eclass에 있는 TodoList을 crawling해서 원하는 항목을 설정한 시간마다 디스코드 채널에 채팅으로 기한이 얼마나 남았는지 알림을 보내줍니다.
### 사용법
1. crawling을 위해 chormedriver을 root directory에 설치해줍니다. Chrome 우상단에 ...을 클릭한 뒤 Chrome 정보에 들어가면 버전을 확인할 수 있습니다. 버전에 맞는 드라이버를 설치하시면 됩니다. 
1. discord 서버에 들어오셔서 reminder 채널에 접속해 주시면 됩니다.
[초대 링크](https://discord.gg/T6SjQjQV)
1. (코드) os.environ("") 이 부분을 string으로 eclass id와 비번을 입력해줍니다.
1. 파이썬 파일(reminder_bot.py)을 실행합니다.
1. discord 채널에 접속해 /활성화, /재설정 명령어를 채팅으로 입력해줍니다. 
### 프로그램 기능
1. /활성화
2. /재설정
## Example

## Conclusion
