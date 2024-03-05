import sys
import helper
import traceback

print('num of arguments: ', len(sys.argv))
#print(sys.argv)


input_args = sys.argv
#print('consumer_key: ', input_args[1])
try:
	new_tweet_to_send = helper.prep_tweet(fn_df_of_puts='puts_by_stock.csv', 
		fn_df_twitter_handles='df_company_info2_backup.csv', 
		fn_df_of_sent_tweets='sent_tweets_db.csv', fn_df_recent_stock_data='data_by_stocks.csv')
	helper.send_tweet_with_pytwitter(tweet_text=new_tweet_to_send,
			consumer_key_=str(input_args[1]), consumer_secret_=str(input_args[2]),
			access_token_=str(input_args[3]), access_token_secret_=str(input_args[4]))
except:
	print('Error in Sending Tweets: ')
	traceback.print_exc()


