import sys
import helper
import traceback

print('num of arguments: ', len(sys.argv))
#print(sys.argv)


input_args = sys.argv
#print(input_args[1])
try:
	helper.send_tweet(tweet_text='Automated Test Tweet',
			consumer_key_=str(input_args[1]), consumer_secret_=str(input_args[2]),
			access_token_=str(input_args[3]), access_token_secret_=str(input_args[4]))
except:
	print('Error in Sending Tweets: ')
	traceback.print_exc()


