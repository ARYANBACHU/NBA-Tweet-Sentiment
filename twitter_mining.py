import string
import tweepy
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

load_dotenv()
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
if BEARER_TOKEN is None:
    print("No token found. Check your .env file.")
    exit()
client = tweepy.Client(bearer_token=BEARER_TOKEN)

#finds 10 most recent tweets with Cade Cunningham in it (in English) and stores the information
response = client.search_recent_tweets(
    query="Cade Cunningham -is:retweet lang:en",
    max_results=10,
    tweet_fields=["created_at"],
)

#print the 10 tweets
for tweet in response.data or []:
    print(tweet.created_at, tweet.text)

# top 10 term frequencies for the 10 Cade posts
stopwords = {"the", "a", "an", "and", "or", "to", "of", "in", "is",
    "it", "for", "on", "with", "this", "that", "i", "you", "my", "be",
    "are", "was", "at", "as", "so", "but", "if", "just", "have"}
word_counts = {}
for tweet in response.data or []:
    text = tweet.text.lower()
    words = text.split()
    for word in words:
        if word.startswith("http") or word.startswith("@"):
            continue
        word = word.strip(string.punctuation)
        if word == "" or word in stopwords:
            continue
        if word in word_counts:
            word_counts[word] = word_counts[word] + 1
        else:
            word_counts[word] = 1
sorted_words = sorted(word_counts, key=word_counts.get, reverse=True)
top_counts = []
top_words = sorted_words[:10]
for word in top_words:
    # print(word, word_counts[word])
    top_counts.append(word_counts[word])
#Visualizing Data
plt.figure(figsize=(10, 5))
plt.bar(top_words, top_counts)
plt.title("Most Common Words in Cade Tweets")
plt.xlabel("Word")
plt.ylabel("Frequency")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("word_frequencies.png")
plt.show()

# print 10 of my following
user = client.get_user(username="bachuaryan")
my_id = user.data.id
followers = []
for user in tweepy.Paginator(
    client.get_users_following,
    id=my_id,
    max_results=10,
    user_fields=["username", "created_at"],
).flatten(limit=10):
    followers.append(user)
    print(user.username)
print("Total fetched:", len(followers))

