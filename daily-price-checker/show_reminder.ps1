$fn = [string]([char]0x05D9 + [char]0x05D5 + [char]0x05DE + [char]0x05D9 + ".csv")
$message = "Daily Benda Price Checker Reminder:`r`n`r`nPlease make sure the daily CSV file is uploaded to C:\Temp\" + $fn + ".`r`n`r`nThen open the chat and ask the agent to run the price comparison."
msg * /time:0 $message

