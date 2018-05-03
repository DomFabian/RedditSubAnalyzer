import praw

reddit = praw.Reddit(user_agent='<removed>',
                     client_id='<removed>',
                     client_secret='<removed>',
                     username='<removed>',
                     password='<removed>')
reddit.read_only = True                 

aggies = reddit.subreddit('aggies')

list_of_subs_with_duplicates = []
seen_redditors = []

def mine_used_subs(author):
    global reddit

    # skip all redditors already seen
    global seen_redditors
    if author in seen_redditors:
        return []
    
    posts = reddit.redditor(author).submissions.top('year')
    comments = reddit.redditor(author).comments.top('year')

    used_subs = []

    # search through the author's posts...
    for post in posts:
        post_sub = str(post.subreddit)

        # do not allow duplicates in used_subs
        if post_sub not in used_subs:
            used_subs.append(post_sub)

    # ...and their comments
    for comment in comments:
        comment_sub = str(comment.subreddit)

        # do not allow duplicates in used_subs
        if comment_sub not in used_subs:
            used_subs.append(comment_sub)

    return used_subs

counter = 0
for submission in aggies.top('day'):
    counter += 1
    if counter > 100:
        break
    try:
        # search the author of the post
        author = submission.author.name
        used_subs = mine_used_subs(author)
        seen_redditors.append(author)

        # search the authors of the comments on the post
        for comment in submission.comments.list():
            author = comment.author.name
            used_subs += mine_used_subs(author)
            seen_redditors.append(author)
    
    except:
        continue

    list_of_subs_with_duplicates += used_subs

list_of_subs = {}
# convert list with duplicates into dictionary (inefficiently)
for subreddit in list_of_subs_with_duplicates:
    list_of_subs[subreddit] = 0
for subreddit in list_of_subs_with_duplicates:
    list_of_subs[subreddit] += 1

filename = 'export.csv'
export = open(filename, 'w+')
export.write('Subreddit:,Frequency:\n')
for key, value in list_of_subs.items():
    export.write(key + ', ' + str(value) + '\n')
export.close()
