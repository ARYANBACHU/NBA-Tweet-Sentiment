import tweepy
import string
import math
import matplotlib.pyplot as plt
from nltk.corpus import opinion_lexicon
from nltk.corpus import stopwords as nltk_stopwords
import os
from dotenv import load_dotenv

MIN_COUNT = 2
load_dotenv()
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
if BEARER_TOKEN is None:
    print("No token found. Check your .env file.")
    exit()
client = tweepy.Client(bearer_token=BEARER_TOKEN)

#get the tweets
response = client.search_recent_tweets(
    query="(NBA OR #NBA OR @NBA) -is:retweet -is:reply -has:links lang:en",
    max_results=100,
    tweet_fields=["created_at"],
)
all_tweets = response.data
if all_tweets is None:
    all_tweets = []
tweets = []
for tweet in all_tweets:
    tweets.append(tweet.text)

#loading sentiment vocabularies
positive_set = set(opinion_lexicon.positive())
negative_set = set(opinion_lexicon.negative())
positive_set.update(["goat", "buckets", "dominant", "unreal", "dawg", "lethal",
    "cooking", "clutch", "cooking", "elite", "mvp"])
negative_set.update(["brick", "bricks", "airball", "choke", "choked", "flop", "flopping",
    "washed", "overrated", "tanking", "fraud", "turnover", "turnovers"])
negative_set.discard("nasty")
positive_set.add("nasty")

#making list of words that we don't care about to have better top 10 data
stopwords = set(nltk_stopwords.words("english"))
extra_stopwords = ["nba", "rt", "lol", "just", "get", "one", "really",
    "actually", "even", "already", "day", "honestly", "amp", "u", "im",
    "dont", "ive", "gonna", "got", "lot", "left"]
stopwords.update(extra_stopwords)
stopwords = stopwords - positive_set - negative_set

#counting term frequencies and co-occurences
term_freq = {}
co_oc = {}
for text in tweets:
    words = text.lower().split()
    clean_words = []
    #loop through all words and clean word list of tweet
    for word in words:
        if word.startswith("http") or word.startswith("@"):
            continue
        word = word.strip(string.punctuation)
        if word == "" or word in stopwords:
            continue
        clean_words.append(word)

    #up frequency for every unique word in tweet
    unique_words = set(clean_words)
    for term in unique_words:
        term_freq[term] = term_freq.get(term, 0) + 1
    
    #save positions of sentiment words
    sentiment_positions = []
    for i in range(len(clean_words)):
        if clean_words[i] in positive_set or clean_words[i] in negative_set:
            sentiment_positions.append(i)

    #pairs each word to its closest sentiment word
    pairs = set()
    for i in range(len(clean_words)):
        term = clean_words[i]
        closest_senti = None
        closest_dist = 1000
        for j in sentiment_positions:
            if clean_words[j] == term:
                continue
            curr_dist = abs(i - j)
            if curr_dist < closest_dist:
                closest_dist = curr_dist
                closest_senti = clean_words[j]
        if closest_senti is not None:
            pairs.add((term, closest_senti))

    #keep track of occurences of pairs
    for pair in pairs:
        co_oc[pair] = co_oc.get(pair, 0) + 1

#compute PMI and Sematic Orientation
semantic_orientation = {}
for pair, pair_count in co_oc.items():
    term = pair[0]
    senti = pair[1]
    num_tweets = len(tweets)

    #compare probabilities of how often the two words appear together
    #to how often you would expect by pure chance
    prob_term = term_freq[term] / num_tweets
    prob_senti = term_freq[senti] / num_tweets
    prob_joint = pair_count / num_tweets
    pmi = math.log2(prob_joint / (prob_term * prob_senti))

    #add or subtract the pmi based on the connotation
    if senti in positive_set:
        change = pmi
    else:
        change = -pmi
    semantic_orientation[term] = semantic_orientation.get(term, 0) + change

#rank the terms
strong_terms = {}
for term in semantic_orientation:
    if term in positive_set or term in negative_set:
        continue
    if term_freq[term] < MIN_COUNT:
        continue
    strong_terms[term] = semantic_orientation[term]
sorted_terms = sorted(strong_terms, key=strong_terms.get, reverse=True)
most_pos = sorted_terms[:10]
most_neg = sorted_terms[-10:]
print("\nMost Positive Terms:")
for term in most_pos:
    print(term, round(strong_terms[term], 4), "(in", term_freq[term], "tweets)")
print("\nMost Negative Terms:")
for term in reversed(most_neg):
    print(term, round(strong_terms[term], 4), "(in", term_freq[term], "tweets)")

#terms I'm checking to analyze their sentiment
print("\nTerms I'm checking")
checking = ["contract", "lottery", "lebron", "76ers", "refs", "curry", ]
for term in checking:
    if term in semantic_orientation:
        print(term, round(semantic_orientation[term], 4))
    else:
        print(term, "not found")

#chart to visualize data
labels = most_pos + most_neg
scores = []
colors = []
for term in most_pos:
    scores.append(strong_terms[term])
    colors.append("green")
for term in most_neg:
    scores.append(strong_terms[term])
    colors.append("red")
plt.figure(figsize=(12, 5))
plt.bar(labels, scores, color=colors)
plt.axhline(0, color="black")
plt.title("Semantic Orientation of Terms in NBA Tweets")
plt.ylabel("Semantic Orientation")
plt.xticks(rotation=60)
plt.tight_layout()
plt.savefig("semantic_orientation.png")
plt.show()