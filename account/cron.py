from .models import *
from django.contrib.sessions.models import Session

def update_daily_limit():
    limit_data = document_limit.objects.all()
    for data in limit_data:
        total_limit = data.limit
        data.remaining_limit = total_limit
        data.save()
		
def logout_all_users(self):
    #print("Entering Logout fun")
    user_data = User.objects.all()
    for i in user_data:
        session_key = i.session_key
        #print("KEY ->", session_key)
        try:
            session_data = Session.objects.get(session_key=session_key)
            session_data.delete()
            #print("Deleted Key")
        except:
            pass
        i.session_key = ''
        i.save()
    try:
        session_data = Session.objects.all()
        for sess in session_data:
            #print("Delete other session - ", sess.session_key)
            sess.delete()
    except:
        pass
