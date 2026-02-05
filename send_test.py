import requests

r = requests.post(
    'https://api.telegram.org/bot8479703528:AAFG2p9UsAC65_3IMm2aCvw9klvFTjJ5lvc/sendMessage',
    json={
        'chat_id': 159306920,
        'text': '🤖 בוט התראות רעידות אדמה פעיל!\n\nתקבל התראות על רעידות אדמה מכל העולם עם:\n• עוצמה\n• מיקום מדויק\n• מרחק מישראל\n• קואורדינטות\n• קישור למפה\n\nמקור הנתונים: USGS'
    }
)
print("ok:", r.json().get("ok"))
