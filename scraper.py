import sys
import praw
import prawcore

class Bot(object):

    ''' \param reddit: the praw instance of reddit

        \param debug: boolean value for enabling logging to stdout

        \param subreddit: the praw instance of the subreddit that is currently
                under investigation

        \param depth: the length of time in question for the subreddit. can be
                'hour', 'day', 'week', 'month', 'year', or 'all'

        \param seen_redditors: a maintainanble list of all of the unique 
                redditors seen
                
        \param subreddit_dict: a maintainable dictionary of all of the 
                subreddits seen with the corresponding number of times it
                has been seen
    '''
    def __init__(self, reddit, debug=True):
        self.reddit = reddit
        self.debug = debug
        self.subreddit = None
        self.subreddit_depth = None
        self.redditor_depth = None
        self.seen_redditors = []
        self.subreddit_dict = {}


    ''' whitelist the allowed depth parameters. defaults to 'week'.

        \arg depth: a string representing how far back to look
    '''
    @staticmethod
    def __validate_depth(depth):
        if depth in ['hour', 'day', 'week', 'month', 'year', 'all']:
            return depth
        else:
            return 'week'


    ''' return a list of all of the redditors that have posted in
        or commented in a subreddit in the past year.
        
        \arg depth: a string representing how far back to look
    '''
    @staticmethod
    def get_redditors_for_subreddit(subreddit, depth):

        depth = Bot.__validate_depth(depth)
        
        redditors = []

        for submission in subreddit.top(depth):
            
            # add the redditor that created the post
            redditors.append(submission.author)

            # add the redditors that commented on the post
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                redditors.append(comment.author)

        # return only the unique list of redditors that are not None
        redditors = list(set(redditors))
        return [r for r in redditors if r is not None]


    ''' return a list of unique subreddits used by a redditor in the 
        past year. this includes all of the subreddits that they have 
        posted in and commented in.

        \arg depth: a string representing how far back to look
    '''
    @staticmethod
    def get_used_subs_for_redditor(redditor, depth):

        depth = Bot.__validate_depth(depth)

        # look only at the redditor's past 'depth' of activity
        posts = redditor.submissions.top(depth)
        comments = redditor.comments.top(depth)

        used_subreddits = []

        for post in posts:
            used_subreddits.append(post.subreddit)

        for comment in comments:
            used_subreddits.append(comment.subreddit)

        # return only the unique list of subreddits
        return list(set(used_subreddits))


    ''' take in all of the information about a given subreddit. 

        \arg subreddit_depth: a string representing how far back to look 
            in the given subreddit. defaults to 'week'

        \arg redditor_depth: a string representing how far back to look in
            each redditor's history. defaults to 'year'
    '''
    def profile_subreddit(self, subreddit, subreddit_depth='week', redditor_depth='year'):

        # accept both a string and the praw subreddit object
        if isinstance(subreddit, str):
            subreddit = self.reddit.subreddit(subreddit)
        self.subreddit = subreddit

        self.subreddit_depth = Bot.__validate_depth(subreddit_depth)
        self.redditor_depth = Bot.__validate_depth(redditor_depth)

        if self.debug:
            print('Loading information for r/{}...'.format(subreddit.display_name))

        self.seen_redditors = Bot.get_redditors_for_subreddit(subreddit, self.subreddit_depth)
        num_redditors = len(self.seen_redditors)

        if self.debug:
            print("Found {} redditors that used r/{} in the last '{}'.".format(
                num_redditors, subreddit.display_name, self.subreddit_depth))

        seen_subreddits = []

        redditor_count = 1
        error_count = 0
        for redditor in self.seen_redditors:

            if self.debug:
                print("({}/{}) Analyzing u/{}'s account...".format(redditor_count, 
                    num_redditors, redditor.name)),

            try:
                used_subs = Bot.get_used_subs_for_redditor(redditor, self.redditor_depth)

            # handle 403 Restricted HTTP Response
            except prawcore.exceptions.Forbidden:
                if self.debug:
                    print('ERROR.')
                error_count += 1
                redditor_count += 1
                continue

            if self.debug:
                print('done.')
            
            seen_subreddits += used_subs
            redditor_count += 1

        if self.debug:
            print('Assembling internal data structures...'),

        # assemble the frequency dictionary of seen subreddits, by string display_name
        for sub in list(set(seen_subreddits)):
            self.subreddit_dict[sub.display_name] = 0
        for sub in seen_subreddits:
            self.subreddit_dict[sub.display_name] += 1

        if self.debug:
            print('done.')

        # print some summary statistics
        print('')
        print('Summary of findings:')
        print('\tSuccessfully analyzed {}/{} unique Redditors found in r/{}.'.format(
            num_redditors - error_count, num_redditors, self.subreddit))
        print('\tDiscovered {} unique subreddits used by members of r/{}.'.format(
            len(self.subreddit_dict), self.subreddit))


    ''' create a .csv file that documents all of the subreddits found.

        \arg verbose: boolean to define how much output on each subreddit

        default columns for each subreddit are:
        - subreddit display name
        - frequency

        verbose columns for each subreddit are:
        - NSFW status
        - subscriber count
    '''
    def output_results(self, filename='output.csv', verbose=False):
        out_file = open(filename, 'w+')

        # output the headers
        out_file.write('Subreddit,Frequency')
        if verbose:
            out_file.write(',NSFW,Subscribers')
        out_file.write('\n')
        
        # output the data rows
        for subreddit_name, frequency in self.subreddit_dict.items():
            out_file.write(subreddit_name + ',' + str(frequency))

            # write out verbose columns
            subreddit = self.reddit.subreddit(subreddit_name)
            if verbose:
                out_file.write(',')
                out_file.write('true,' if subreddit.over18 else 'false,')
                out_file.write(str(subreddit.subscribers))
            
            out_file.write('\n')
    
        out_file.close()


# example main
if __name__ == '__main__':

    # configure praw reddit instance
    reddit = praw.Reddit('AggieBot')
    reddit.read_only = True

    # instantiate the AggieBot
    aggiebot = Bot(reddit)

    aggiebot.profile_subreddit('aggies', subreddit_depth='hour', redditor_depth='all')
    aggiebot.output_results(verbose=True)

    print('Analysis complete!')
