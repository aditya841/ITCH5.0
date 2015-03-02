1. Stock_files.tar.gz: It contains ".xlsx" files for each stock. Each stock file contains VWAP calculations for it.
2. main.py: Python program to parse through data
3. stock_dictionary.d: It contains the dictionary that keep all records of all transactions, with stock-name as key

** XlsxWriter library is needed for running this program
** I have used Python 2.7.6 for running this program

Explanation:
Decoding: 
The struct library of Python is used to decode the byte order messages.

Parsing:
I have parsed both type of Add Order messages and recorded the stock-name and stock-price in a dictionary, object_list, with order-reference-number as key. *We only parse "Buy" order messages, to avoid double-counting.

The Delete Order message helps us to clear the object_list of unnecessary order-reference-numbers.

The Replace Order message replaces the old order-reference-number with new ones, also replacing the stock-price.

The two kinds of Order Executed messages get the stock-name from the object_list, by accessing the record associated to the order-reference-number. Also the Order Executed message without price, gets its price from the object_list. We add these transactions to stock_map, which has stock-name as key. We record type of message, order-reference-number, stock-price, share-volume for each transaction. We also add these transactions to executing_order_map, for easy reference when removing transactions due to Break Messages. *We only parse "Printable" transactions for our purposes.

The Trade messages are also parsed similar to Order Executed messages. Instead of the order-reference-number, we store the match-number for identification purpose when removing the transaction.

The Cross Trade messages are also parsed. They are similar to Trade messages.

Calculation:
VWAP = Cumulative(Price * Volume) / Cumulative(Volume)

Storage and Printing:
I have used Pickle library to compress and store the final dictionary.

I have used the XlsxWriter library to write the stock-files.
