from django.http import JsonResponse
from bson import ObjectId
from datetime import datetime
from .mongo_client import topics_collection, entries_collection, activities_collection 
# from .db import topics_collection, entries_collection

from django.shortcuts import render
from django.shortcuts import render, redirect

def home(request):
    """Redirect to login or topics depending on auth"""
    username = request.COOKIES.get("username")
    if username:
        return redirect('topics_page')
    else:
        return redirect('login_page')


def topics_page(request):
    """Render the topics page only if logged in"""
    username = request.COOKIES.get("username")
    if not username:
        return redirect('login_page')
    return render(request, 'topics.html')


def entries_page(request):
    """Render the entries page only if logged in"""
    username = request.COOKIES.get("username")
    if not username:
        return redirect('login_page')
    return render(request, 'entries.html')

def add_topic(request):
    """Add a new topic (like 'Machine Learning' or 'Chess')."""
    username = request.COOKIES.get("username")
    if not username:
        return JsonResponse({"error": "Not logged in"}, status=401)

    topic_text = request.GET.get("text")
    if not topic_text:
        return JsonResponse({"error": "Missing 'text' parameter."}, status=400)

    topic = {
        "text": topic_text,
        "username": username,
        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    result = topics_collection.insert_one(topic)
    return JsonResponse({
        "message": "Topic added successfully!",
        "topic_id": str(result.inserted_id)
    })


def get_topics(request):
    """Get all topics for the logged-in user."""
    username = request.COOKIES.get("username")
    if not username:
        return JsonResponse({"error": "Not logged in"}, status=401)

    data = list(topics_collection.find({"username": username}, {"_id": 1, "text": 1, "date_added": 1}))
    for topic in data:
        topic["_id"] = str(topic["_id"])
    return JsonResponse(data, safe=False)



def add_entry(request):
    """Add an entry under a specific topic using topic_id."""
    topic_id = request.GET.get("topic_id")
    entry_text = request.GET.get("text")
    username = request.COOKIES.get("username")   # ✅ GET USERNAME

    if not topic_id or not entry_text:
        return JsonResponse({"error": "Both 'topic_id' and 'text' are required."}, status=400)

    if not username:
        return JsonResponse({"error": "User not logged in, username missing in cookies."}, status=401)

    try:
        topic_obj_id = ObjectId(topic_id)
    except Exception:
        return JsonResponse({"error": "Invalid topic_id format."}, status=400)

    # Check if topic exists
    topic = topics_collection.find_one({"_id": topic_obj_id})
    if not topic:
        return JsonResponse({"error": "Topic not found."}, status=404)

    entry = {
        "topic_id": topic_obj_id,
        "text": entry_text,
        "username": username,   
        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    entries_collection.insert_one(entry)
    return JsonResponse({"message": "Entry added successfully!"})



def get_entries(request):
    """Get all entries for a given topic."""
    topic_id = request.GET.get("topic_id")

    if not topic_id:
        return JsonResponse({"error": "Missing 'topic_id' parameter."}, status=400)

    try:
        topic_obj_id = ObjectId(topic_id)
    except Exception:
        return JsonResponse({"error": "Invalid topic_id format."}, status=400)

    entries = list(entries_collection.find(
        {"topic_id": topic_obj_id},
        {"_id": 0, "text": 1, "date_added": 1}
    ))

    return JsonResponse(entries, safe=False)


def topics_page(request):
    """Render the topics.html page."""
    return render(request, 'topics.html')

def entries_page(request):
    """Render the entries.html page."""
    return render(request, 'entries.html')



import hashlib
from django.http import JsonResponse
from .mongo_client import users_collection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(request):
    """Register a new user"""
    username = request.GET.get("username")
    password = request.GET.get("password")

    if not username or not password:
        return JsonResponse({"error": "Username and password required"}, status=400)

    if users_collection.find_one({"username": username}):
        return JsonResponse({"error": "Username already exists"}, status=400)

    users_collection.insert_one({
        "username": username,
        "password": hash_password(password)
    })
    return JsonResponse({"message": "User registered successfully!"})

def login_user(request):
    """Login a user"""
    username = request.GET.get("username")
    password = request.GET.get("password")

    if not username or not password:
        return JsonResponse({"error": "Username and password required"}, status=400)

    user = users_collection.find_one({"username": username})
    if not user or user["password"] != hash_password(password):
        return JsonResponse({"error": "Invalid username or password"}, status=401)

    # Simulate a session using cookies
    response = JsonResponse({"message": "Login successful!"})
    response.set_cookie("username", username)
    return response

def logout_user(request):
    """Logout user"""
    response = JsonResponse({"message": "Logged out successfully"})
    response.delete_cookie("username")
    return response

def login_page(request):
    return render(request, 'login.html')

def register_page(request):
    return render(request, 'register.html')

# username = request.COOKIES.get("username") 
# topics = list(topics_collection.find({"username": username}))
from .utils.activity_graph import ActivityGraph

from .mongo_client import activities_collection

def view_topic(request, topic_id):
    username = request.COOKIES.get("username")
    if not username:
        return redirect("/login/")

    topic = topics_collection.find_one({"_id": ObjectId(topic_id)})
    entries = list(entries_collection.find({"topic_id": ObjectId(topic_id)}))

    tracker = ActivityGraph(activities_collection, username)
    tracker.add_activity(topic["text"])

    return render(request, "view_topic.html", {"topic": topic, "entries": entries})




from django.shortcuts import render, redirect
from .utils.activity_graph import ActivityGraph
 # adjust import if needed
def activity_view(request):
    username = request.COOKIES.get("username")
    if not username:
        return redirect("/login/")

    tracker = ActivityGraph(activities_collection, username)
    activity_raw = tracker.sorted_topics()

    activity_data = [
        {"topic": item["topic"], "count": item["count"]}
        for item in activity_raw
    ]

    return render(request, "activity.html", {"activity_data": activity_data})


