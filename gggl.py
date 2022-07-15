# importing the datetime package  
import datetime  
  
# given epoch time  
epoch_time = 1657768972094  
  
# using the datetime.fromtimestamp() function  
date_time = datetime.datetime.fromtimestamp( epoch_time/1000 )  
  
# printing the value  
print("Given epoch time:", epoch_time)  
print("Converted Datetime:", date_time )  