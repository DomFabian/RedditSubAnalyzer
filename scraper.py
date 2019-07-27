import sys
import praw

class AggieBot(object):

    ''' \param reddit: the praw instance of reddit

        \param seen_redditors: a maintainanble list of all of the unique 
                redditors seen
                
        \param subreddit_dict: a maintainable dictionary of all of the 
                subreddits seen with the corresponding number of times it
                has been seen
        
        \params debug: boolean value for enabling logging to stdout
    '''
    def __init__(self, reddit, debug=False):
        self.reddit = reddit
        self.seen_redditors = []
        self.subreddit_dict = {}
        self.debug = debug


    ''' return a list of all of the redditors that have posted in
        or commented in a subreddit in the past year. '''
    def get_redditors_for_subreddit(self, subreddit):
        
        redditors = []

        for submission in subreddit.top('month'):
            
            # add the redditor that created the post
            redditors.append(submission.author)

            # add the redditors that commented on the post
            for comment in submission.comments:
                try:
                    redditors.append(comment.author)
                except AttributeError:
                    break

        # return only the unique list of redditors
        return list(set(redditors))


    ''' return a list of unique subreddits used by a redditor in the 
        past year. this includes all of the subreddits that they have 
        posted in and commented in. '''
    def get_used_subs_for_redditor(self, redditor):

        # handle the case where a null redditor is tried
        if redditor is None:
            return []

        # look only at the redditor's past year of activity
        posts = redditor.submissions.top('year')
        comments = redditor.comments.top('year')

        used_subreddits = []

        for post in posts:
            used_subreddits.append(str(post.subreddit))

        for comment in comments:
            used_subreddits.append(str(comment.subreddit))

        # return only the unique list of subreddits
        return list(set(used_subreddits))


    ''' take in all of the information about a given subreddit. '''
    def load_subreddit(self, subreddit):

        # accept both a string and the praw subreddit object
        if isinstance(subreddit, str):
            subreddit = self.reddit.subreddit(subreddit)

        if self.debug:
            print('Loading information for r/{}...'.format(subreddit.display_name))

        self.seen_redditors = self.get_redditors_for_subreddit(subreddit)
        num_redditors = len(self.seen_redditors)

        if self.debug:
            print('Found {} redditors that used r/{} in the last year.'.format(
                num_redditors, subreddit.display_name))

        seen_subreddits = []

        count = 1
        for redditor in self.seen_redditors:
            # skip all of the invalid redditor objects. these likely
            # come from deleted posts.
            if redditor is None:
                continue

            if self.debug:
                print("({}/{}) Analyzing u/{}'s account...".format(count, num_redditors, redditor.name)),

            try:
                used_subs = self.get_used_subs_for_redditor(redditor)
                print('done.')
            except KeyboardInterrupt:
                print('\nShutting down...')
                sys.exit(0)
            except:
                print('ERROR.')
                continue
            
            seen_subreddits += used_subs
            count += 1

        if self.debug:
            print('Crunching the numbers...')

        # assemble the frequency dictionary of seen subreddits
        for sub in list(set(seen_subreddits)):
            self.subreddit_dict[sub] = 0
        for sub in seen_subreddits:
            self.subreddit_dict[sub] += 1


    ''' create a .csv file that documents all of the subreddits found
        and a frequency count for each one. '''
    def output_results(self, filename='output.csv'):
        out_file = open(filename, 'w+')

        out_file.write('Subreddit,Frequency\n')
        for subreddit_name, frequency in self.subreddit_dict.items():
            out_file.write(subreddit_name + ',' + str(frequency) + '\n')
    
        out_file.close()



if __name__ == '__main__':

    # configure praw reddit instance
    reddit = praw.Reddit('AggieBot')
    reddit.read_only = True

    # instantiate the AggieBot
    aggiebot = AggieBot(reddit, debug=True)

    aggiebot.load_subreddit('all')
    aggiebot.output_results()

    print('comleted successfully')
