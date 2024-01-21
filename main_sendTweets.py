import sys
import helper

print('num of arguments: ', len(sys.argv))
input_args = sys.argv
helper.send_tweet(tweet_text='Automated Test Tweet',
			consumer_key_=input_args[0], consumer_secret_=input_args[1],
			,consumer_secret_=input_args[2],access_token_,access_token_secret=input_args[3])

