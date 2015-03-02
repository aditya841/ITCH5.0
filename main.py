import struct
import pickle
import xlsxwriter

tick_count = 0
executed_order_count = 0
trade_message_count = 0
cross_trade_message_count = 0
object_list = {}
stock_map = {}
executing_order_map = {}

f = open("06022014.NASDAQ_ITCH50", "r");

def add_order_message(message):
	global object_list

	if message[19:20] == 'B':#if buy order
		order_ref_no = struct.unpack("!Q", message[11:19])[0]
		stock_name = message[24:32].strip()
		stock_price = (struct.unpack("!I", message[32:36])[0]) / 10000.00 #to get the four decimal places
		#adding order to dictionary for tracking stock name in executed orders
		object_list[order_ref_no] = (stock_name, stock_price)
	return

def replace_order_message(message):
	global object_list
	old_order_ref_number = struct.unpack("!Q", message[11:19])[0]
	new_order_ref_number = struct.unpack("!Q", message[19:27])[0]
	try:
		(stock_name, stock_price) = object_list.pop(old_order_ref_number)
		object_list[new_order_ref_number] = (stock_name, stock_price)
	except KeyError as e:
		return
	return

def delete_order_message(message):
	global object_list
	order_ref_no = struct.unpack("!Q", message[11:19])[0]
	try:
		object_list.pop(order_ref_no)
	except KeyError as e:
		return		

def executed_price_order_message(message):
	global executed_order_count
	global stock_map
	global object_list
	global executing_order_map

	mType = 'C'
	##check printable order or not
	if message[31:32] == 'Y':	
		order_ref_no = struct.unpack("!Q", message[11:19])[0]
		stock_price = (struct.unpack("!I", message[32:36])[0]) / 10000.00		
		share_volume = struct.unpack("!I", message[19:23])[0]
		match_number = struct.unpack("!Q", message[23:31])[0]
		try:
			(stock_name, stock_price_old) = object_list[order_ref_no]
			if stock_name not in stock_map:
				stock_map[stock_name] = [(mType, order_ref_no, stock_price, share_volume)]			
			else:
				stock_list = stock_map[stock_name]								
				stock_list.append((mType, order_ref_no, stock_price, share_volume))
				stock_map[stock_name] = stock_list
			#add order to executed order map
			executing_order_map[match_number] = (mType, order_ref_no, stock_name)
			executed_order_count+=1		
		except KeyError as e:
			# print "Order number: " . str(order_ref_no)
			# raw_input("Did not find key in object list. Press Enter to continue...")
			return

def executed_order_message(message):
	global executed_order_count
	global stock_map
	global object_list
	global executing_order_map

	mType = 'E'
	order_ref_no = struct.unpack("!Q", message[11:19])[0]
	stock_price = 0
	share_volume = struct.unpack("!I", message[19:23])[0]
	match_number = struct.unpack("!Q", message[23:31])[0]
	try:
		(stock_name, stock_price) = object_list[order_ref_no]
		if stock_name not in stock_map:
			stock_map[stock_name] = [(mType, order_ref_no, stock_price, share_volume)]
		else:
			stock_list = stock_map[stock_name]			
			stock_list.append((mType, order_ref_no, stock_price, share_volume))
			stock_map[stock_name] = stock_list
		#add order to executed order map
		executing_order_map[match_number] = (mType, order_ref_no, stock_name)
		executed_order_count+=1
	except KeyError as e:
		# print "Order number: " . str(order_ref_no)
		# raw_input("Did not find key in object list. Press Enter to continue...")
		return	

def trade_message(message):
	global trade_message_count
	global stock_map
	global object_list
	global executing_order_map

	mType = 'P'
	trade_message_count+=1
	stock_price = (struct.unpack("!I", message[32:36])[0]) / 10000.00
	share_volume = struct.unpack("!I", message[20:24])[0]
	match_number = struct.unpack("!Q", message[23:31])[0]
	stock_name = message[24:32]	
	if stock_name not in stock_map:
		stock_map[stock_name] = [(mType, match_number, stock_price, share_volume)]
	else:
		stock_list = stock_map[stock_name]		
		stock_list.append((mType, match_number, stock_price, share_volume))
		stock_map[stock_name] = stock_list
	#add order to executed order map
	executing_order_map[match_number] = (mType, match_number, stock_name)

def cross_trade_message(message):
	global cross_trade_message_count
	global stock_map
	global object_list
	global executing_order_map
	
	mType = 'Q'
	stock_price = (struct.unpack("!I", message[27:31])[0]) / 10000.00
	share_volume = struct.unpack("!Q", message[11:19])[0]	
	match_number = struct.unpack("!Q", message[31:39])[0]
	stock_name = message[19:27]
	if share_volume == 0:
		return	
	elif stock_name not in stock_map:
		stock_map[stock_name] = [(mType, match_number, stock_price, share_volume)]
	else:
		stock_list = stock_map[stock_name]		
		stock_list.append((mType, match_number, stock_price, share_volume))
		stock_map[stock_name] = stock_list
	#add order to executed order map
	executing_order_map[match_number] = (mType, match_number, stock_name)
	cross_trade_message_count+=1

def broken_trade_message(message):
	global stock_map
	global object_list
	global executing_order_map

	match_number = struct.unpack("!Q", message[11:19])[0]
	try:
		(mType, order_ref_no, stock_name) = executing_order_map.pop(match_number)		
		if stock_name in stock_map:		
			stock_list = stock_map[stock_name]
			for index, item in enumerate(stock_list):
				if item[1] == order_ref_no and mType == item[0]:
					del stock_list[index]
					break
			stock_map[stock_name] = stock_list
	except KeyError as e:		
		return		


def unpack_message(message, mType):	
	if mType == 'A' or mType == 'F':		
		add_order_message(message)		
	elif mType == 'U':		
		replace_order_message(message)
	elif mType == 'D':		
		delete_order_message(message)
	elif mType == 'C':		
		executed_price_order_message(message)		
	elif mType == 'E':		
		executed_order_message(message)
	elif mType == 'P':		
		trade_message(message)		
	elif mType == 'Q':		
		cross_trade_message(message)		
	elif mType == 'B':		
		broken_trade_message(message)
	else:
		return

while(True):	
	length_bytes = f.read(2)
	if not length_bytes:
		break
	packet_length = struct.unpack('!H', length_bytes)[0]
	packet_payload = f.read(packet_length)
	if not packet_payload:
		break
	tick_count+= 1	
	unpack_message(packet_payload, packet_payload[0])

print "Writing data to files......"

output_file = open('output_file.txt', 'a')
output_file.write("Total number of ticks: " + str(tick_count))
output_file.write("Total number of executed orders: " + str(executed_order_count))
output_file.write("Total number of trade messages: " + str(trade_message_count))
output_file.write("Total number of cross trade message: " + str(cross_trade_message_count))

pickle.dump(stock_map, open("stock_dictionary.d", "wb"))

del executing_order_map
del object_list

for key, value in stock_map.iteritems():
	workbook = xlsxwriter.Workbook(key + ".xlsx")
	worksheet = workbook.add_worksheet()
	cumulative_volume = 0
	cumulative_volume_price = 0
	worksheet.write('A1', "Price")
	worksheet.write('B1', "Volume")
	worksheet.write('C1', "Cumulative Volume")
	worksheet.write('D1', "Cumulative Volume * Price")
	worksheet.write('E1', "VWAP")	
	for index, item in enumerate(value):
		worksheet.write("A"+str(index+2), item[2])
		worksheet.write("B"+str(index+2), item[3])
		cumulative_volume+=item[3]
		cumulative_volume_price+= item[2] * item[3]
		worksheet.write("C"+str(index+2), cumulative_volume)
		worksheet.write("D"+str(index+2), cumulative_volume_price)
		worksheet.write("E"+str(index+2), cumulative_volume_price / (cumulative_volume * 1.00))
