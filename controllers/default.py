# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
import re
from datetime import timedelta
import datetime, time


pattern = re.compile(r"""
			\[(?P<time>.*?)\]
#			\s(?P<mac>[0-9A-F]{2}[:]{5}[0-9A-F]{2})?)
			\s(?P<mac>[0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2})
			\s(?P<more>.*)
			\s*"""
			, re.VERBOSE)

def index():
	from datetime import datetime
	#form = SQLFORM(db.station)
	#form = SQLFORM(db.log)
	form = crud.create(db.log)
	if form.process(dbio=False).accepted:
		form.vars.log_id = db.log.insert(**dict(form.vars))
		request.vars.log_file.file.seek(0)
		count=0
		for line in request.vars.log_file.file:
			#print 'l', line
			match = pattern.findall(line)	
			if match:
				d = datetime.strptime(match[0][0], '%m/%d/%y %H:%M:%S')
				db.record.insert(log_id=form.vars.log_id, 
						station_id=form.vars.station_id,
						mac=match[0][1], 
						gathered_on=d)			
				count += 1
		session.flash = 'Inserted %s record' % count
		redirect(URL(f='read', vars={'id':form.vars.station_id}))
	return dict(form=form)

def add_station():
	form = crud.create(db.station)
	if form.process(dbio=True).accepted:
		session.flash = 'Station insert correctly'
		redirect(URL(f='index'))
	return response.render('default/index.html', dict(form=form))



def insert():
	file_stream = open("/home/pvalleri/Desktop/test/bluelog.log", "r")
	matches=[]
	for line in file_stream:
		match = pattern.findall(line)	
		if match:
			d = datetime.strptime(match[0][0], '%m/%d/%y %H:%M:%S')
			db.record.insert(mac=match[0][1], gathered_on=d)	
	return 'done'
	
def read():
	try:	query = db.record.station_id == int(request.vars.id)
	except: 
		request.flash= 'ID not valid'
		return 'error'
	rows = db(query).select(db.record.gathered_on, db.record.gathered_on.epoch())
	info = {'n': len(rows), 'start': rows[0].record.gathered_on, 'end': 'vuoto'}
	return dict(info=info)

def compare():
	return response.render('default/compare.html', {})

# external request, might be ajax too
def get_lines():
	id_start = 17
	id_end = 18
	line_type = request.vars.type
	block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 900
#	if len(request.args) < 2:
#		request.flash= 'ID not valid'
#		return 'error'
#	try:	
#		id_start = int (request.args(0))	
#		id_end = int (request.args(1))
#		block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 500
#		line_type = request.vars.type 
#	except: 
#		request.flash= 'ID not valid'
#		return 'error'
#	if line_type == 'median':
	logs = [{'id_start':11, 'id_end':12},
		{'id_start':15, 'id_end':16},
		{'id_start':19, 'id_end':20},
		{'id_start':17, 'id_end':18},
		{'id_start':13, 'id_end':14},]
	#logs = [{'id_start':15, 'id_end':16}]
	
	out={}
	for l in logs:
		dd = __get_median(l['id_start'], l['id_end'], block_seconds, query='compare')
		dd['id'] = dd['id'] + '%s' % l['id_start']
		out['%s' % dd['id']]=dd

	return response.render('generic.json', out)

def origin_destination():
	#try:	
	#	id_start = int (request.args(0))
	#	id_end = int (request.args(1))
	#	block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 500
	#except: 
	#	request.flash= 'ID not valid'
	#	return response.render('default/od.html', {})
	id_start = 11
	id_end = 12
	block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 500


	start = db.record.with_alias('start')
	end = db.record.with_alias('end')
	
	rows = db( (start.station_id == id_start) &
		   (end.station_id == id_end) &
		   (start.mac == end.mac) ).select( cache=(cache.ram, 3600))

	n_start = db( db.record.station_id == id_start).count( cache=(cache.ram, 3600))
	n_end = db( db.record.station_id == id_end).count( cache=(cache.ram, 3600))

	info = {'n': len(rows), 'n_start':n_start, 'n_end':n_end}

	return response.render('default/diff.html', {'info':info})

def diff():
	return dict()	

def get_hour():
	c = db.record.id.count()
	s = db.record.gathered_on.year() | db.record.gathered_on.month() | db.record.gathered_on.day() | db.record.gathered_on.hour() 
	#dd = db.record.gathered_on.timedelta(minutes=30) 
	rows = db(db.record.id > 0).select(db.record.gathered_on.epoch(), c, groupby=s)

	data = [ [ (r[db.record.gathered_on.epoch()] +3600)* 1000, r[c] ] for r in rows]

	return response.render('generic.json', dict(data=data))

def get_minute():
	c = db.record.id.count()
	s = db.record.gathered_on.year() | db.record.gathered_on.month() | db.record.gathered_on.day() | db.record.gathered_on.hour() | db.record.gathered_on.minutes()

	rows = db(db.record.id > 0).select(db.record.gathered_on.epoch(), c, groupby=s)

	data = [ [ (r[db.record.gathered_on.epoch()] +3600)* 1000, r[c] ] for r in rows]
	request.view = 'generic.json'
	return response.render('generic.json', dict(data=data))

def get_both():
	if not request.vars.id:
		request.flash= 'ID not valid'
		return 'error'
	try:	query = db.record.station_id == int(request.vars.id)
	except: 
		request.flash= 'ID not valid'
		return 'error'
	c = db.record.id.count()

	s = db.record.gathered_on.year() | db.record.gathered_on.month() | db.record.gathered_on.day() | db.record.gathered_on.hour()
	#dd = db.record.gathered_on.timedelta(minutes=30) 
	rows = db(query).select(db.record.gathered_on.epoch(), c, groupby=s)

	s_m = db.record.gathered_on.year() | db.record.gathered_on.month() | db.record.gathered_on.day() | db.record.gathered_on.hour() | db.record.gathered_on.minutes()
	rows_m = db(query).select(db.record.gathered_on.epoch(), c, groupby=s_m)

	hours = [ [ (r[db.record.gathered_on.epoch()] +3600)* 1000, r[c] ] for r in rows]
	minutes = [ [ (r[db.record.gathered_on.epoch()] +3600)* 1000, r[c] ] for r in rows_m]
	
	rows = db(query).select(db.record.gathered_on, 
				db.record.gathered_on.epoch(),
				cache=(cache.ram, 3600),
			        cacheable=True)
	block_seconds = 600
	l = []
	first = True
	for pos, r in enumerate(rows):
		if not first and r[db.record.gathered_on] < limit:
			l[len(l)-1].append(r)
		else:
			limit = r[db.record.gathered_on] + datetime.timedelta(seconds=block_seconds)
			l[len(l):] = [[r]]
			first = False
	
	tens = [ [ (block[0][db.record.gathered_on.epoch()]+3600 + block_seconds/2) * 1000, len(block) ] for block in l]	


	return response.render('generic.json', dict(hours=hours,minutes=minutes, tens=tens))

def get_diff():
	id_start = 11
	id_end = 12

#	if len(request.args) < 2:
#		request.flash= 'ID not valid'
#		return 'error'
#	try:	
#		id_start = int (request.args(0))	
#		id_end = int (request.args(1))
#	except: 
#		request.flash= 'ID not valid'
#		return 'error'

	start = db.record.with_alias('start')
	end = db.record.with_alias('end')
	
	rows = db( (start.station_id == id_start) &
		   (end.station_id == id_end) &
		   (start.mac == end.mac) ).select(start.ALL, 
						   end.ALL, 
						   start.gathered_on.epoch(),
						   cache=(cache.ram, 3600),
						   cacheable=True
						   )
					
	logs=[]
	rows_pos = [r for r in rows if (r.end.gathered_on - r.start.gathered_on > datetime.timedelta(0)) and 
					(r.end.gathered_on - r.start.gathered_on < datetime.timedelta(seconds=12000)) ]
	for pos, r in enumerate(rows_pos):
		t = r.end.gathered_on - r.start.gathered_on
		if True or t<datetime.timedelta(seconds=800):		
			logs.append( [ (r[start.gathered_on.epoch()]+3600) * 1000,
				       int(t.total_seconds()) * 1000 ]	)
	all_logs = dict(logs={'data':logs, 'label': 'matches', 'id':'logs'})	

	for seconds in xrange(700, 1000, 100):
		out = __get_lower( id_start, id_end, seconds )
		all_logs[out['id']] = out
	
	for seconds in xrange(700, 1000, 100):
		out_m = __get_median( id_start, id_end, seconds )
		all_logs[out_m['id']] = out_m

	# single trends
	hours = __get_trend(id_start, 3600)
	#tens = __get_trend(id_start, 600)
	fifteens = __get_trend(id_start, 900)
	all_logs['trendstart_h'] = {'data':hours, 'label': 'trend start h', 'id':'trendstart_h', 'yaxis': 2 }
	#all_logs['trendstart_10'] = {'data':tens, 'label': 'trend start 10m', 'id':'trendstart_10', 'yaxis': 2 }
	all_logs['trendstart_15'] = {'data':fifteens, 'label': 'trend start 15m', 'id':'trendstart_15', 'yaxis': 2 }

	hours = __get_trend(id_end, 3600)
	#tens = __get_trend(id_end, 600)
	fifteens = __get_trend(id_end, 900)
	all_logs['trendend_h'] = {'data':hours, 'label': 'trend end h', 'id':'trendend_h', 'yaxis': 2 }
	#all_logs['trendend_10'] = {'data':tens, 'label': 'trend end 10m', 'id':'trendend_10', 'yaxis': 2 }
	all_logs['trendend_15'] = {'data':fifteens, 'label': 'trend end 15m', 'id':'trendend_15', 'yaxis': 2 }

	return response.render('generic.json', all_logs)

# external request, might be ajax too
def get_line():
	id_start = 11
	id_end = 12
	line_type = request.vars.type
	block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 500
#	if len(request.args) < 2:
#		request.flash= 'ID not valid'
#		return 'error'
#	try:	
#		id_start = int (request.args(0))	
#		id_end = int (request.args(1))
#		block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 500
#		line_type = request.vars.type 
#	except: 
#		request.flash= 'ID not valid'
#		return 'error'
	if line_type == 'median':
		out = __get_median(id_start, id_end, block_seconds)
	elif line_type == 'lower':
		out = __get_lower( id_start, id_end, block_seconds )
	elif line_type == 'trendstart':
		out = {'data':__get_trend( id_start, block_seconds ), 'label': 'trend start %ss' % block_seconds , 'id':'trendstart_%s' % block_seconds , 'yaxis': 2 }
	elif line_type == 'trendend':
		out = {'data':__get_trend( id_end, block_seconds ), 'label': 'trend end %ss' % block_seconds , 'id':'trendend_%s' % block_seconds , 'yaxis': 2 }
	else:
		return 'errore'
	out = {out['id']:out}

	return response.render('generic.json', out)


def __get_trend(id_start, block_seconds):
	query = db.record.station_id == id_start
	rows = db(query).select(db.record.gathered_on, 
				db.record.gathered_on.epoch(),
				cache=(cache.ram, 3600),
			        cacheable=True
				)
	l = []
	first = True
	last = 	rows[0]
	for pos, r in enumerate(rows):
		if not first and r[db.record.gathered_on] < limit:
			l[len(l)-1].append(r)

		elif (last[db.record.gathered_on] + (datetime.timedelta(seconds=block_seconds) * 2)) < r[db.record.gathered_on]:
			l.append([last])
			l.append([r])
		else:
			limit = r[db.record.gathered_on] + datetime.timedelta(seconds=block_seconds)
			l.append([r])
			first = False
		last = 	r

	out = [ [ (block[0][db.record.gathered_on.epoch()]+3600 + block_seconds/2) * 1000, len(block) ] for block in l]
	return out
	


def __get_lower( id_start, id_end, block_seconds ):
	start = db.record.with_alias('start')
	end = db.record.with_alias('end')
	
	rows = db( (start.station_id == id_start) &
		   (end.station_id == id_end) &
		   (start.mac == end.mac) ).select(start.ALL, 
						   end.ALL, 
						   start.gathered_on.epoch(),
						   cache=(cache.ram, 3600),
						   cacheable = True)
					
	rows_pos = [r for r in rows if (r.end.gathered_on - r.start.gathered_on > datetime.timedelta(0)) and 
					(r.end.gathered_on - r.start.gathered_on < datetime.timedelta(seconds=12000)) ]
	l = []
	first=True
	prev = rows_pos[0]
	for pos, r in enumerate(rows_pos):
		if not first and r.start.gathered_on < limit:
			l[len(l)-1].append(r)
		elif (prev.start.gathered_on + (datetime.timedelta(seconds=block_seconds) * 2)) < r.start.gathered_on:
			l.append([0, prev])
			l.append([0, r])
		else:
			limit = r.start.gathered_on + datetime.timedelta(seconds=block_seconds)
			l[len(l):] = [[r]]
			first = False
		prev = r

	lower_bound=[]
	for pos, block in enumerate(l):
		if block[0] == 0:
			lower_bound.append ( [(block[1][start.gathered_on.epoch()]+3600 + block_seconds/2) * 1000,
						0] )
		else:		
			cur_min=min([(r.end.gathered_on - r.start.gathered_on) if r != 0 else 0 for r in block ])	
			lower_bound.append ( [(block[0][start.gathered_on.epoch()]+3600 + block_seconds/2) * 1000,
				int(cur_min.total_seconds()) * 1000] )
	
	return {'data': lower_bound,'label':"Lower bound (%ss)" % block_seconds, 'id':'lower_bound_%s' %  block_seconds };


def __get_median( id_start, id_end, block_seconds=800, vertical_block_seconds=20, query=None ):
	start = db.record.with_alias('start')
	end = db.record.with_alias('end')
#	if not query:
#		query = ((start.station_id == id_start) &
#			   (end.station_id == id_end) &
#			   (start.mac == end.mac))
	test = query		
	if query=='compare':
		query = ((start.log_id == id_start) &
			   (end.log_id == id_end) &
			   (start.mac == end.mac))
	else:
		query = ((start.station_id == id_start) &
			   (end.station_id == id_end) &
			   (start.mac == end.mac))
	
	rows = db( query ).select(start.ALL, 
				   end.ALL, 
				   start.gathered_on.epoch(),
				   end.gathered_on.epoch(),
				   orderby=start.gathered_on.epoch(),
				   cache=(cache.ram, 3600),
				   cacheable = True)
					
	rows_pos = [r for r in rows if (r.end.gathered_on - r.start.gathered_on > datetime.timedelta(0)) and 
					(r.end.gathered_on - r.start.gathered_on < datetime.timedelta(seconds=12000)) ]
	l = [] 
	first=True
	prev = rows_pos[0]
	for pos, r in enumerate(rows_pos):
		if not first and r.start.gathered_on < limit:
			l[len(l)-1].append(r)
		elif (prev.start.gathered_on + (datetime.timedelta(seconds=block_seconds) * 2)) < r.start.gathered_on:
			l.append([0, prev])
			l.append([0, r])
		else:
			limit = r.start.gathered_on + datetime.timedelta(seconds=block_seconds)
			l[len(l):] = [[r]]
			first = False
		prev = r

	median=[]
	fdate = l[0][0][start.gathered_on]
	day = datetime.datetime(fdate.date().year, fdate.date().month, fdate.date().day)
	for pos, block in enumerate(l):
		if block[0] == 0:
			if test=='compare':
				mdate = block[1][start.gathered_on]
				seconds = (mdate-day).total_seconds()		
			else:
				seconds = block[1][start.gathered_on.epoch()]
			median.append ( [ (seconds +3600 + block_seconds/2) * 1000,	0] )
		else:
			initial_time_frame = min([(r[end.gathered_on.epoch()] - r[start.gathered_on.epoch()])  for r in block ] )
			end_time_frame = max( [ (r[end.gathered_on.epoch()] - r[start.gathered_on.epoch()])  for r in block ] )
			n_windows = (end_time_frame - initial_time_frame) / vertical_block_seconds		
			windows = [0] * (n_windows + 1)
			values = ''
			#print windows
			if len(block) <= 2:
				print 'WARNING', len(block)

			for ele in block:
				diff = (ele[end.gathered_on.epoch()] - ele[start.gathered_on.epoch()])
				cur_pos = (diff - initial_time_frame)  / vertical_block_seconds
				#print len(windows), cur_pos			
				windows[cur_pos] += 1
			#print windows
			tot = initial_time_frame + (vertical_block_seconds * windows.index(max(windows)))
			if test=='compare':
				mdate = block[0][start.gathered_on]
				seconds = (mdate-day).total_seconds()		
			else:
				seconds = block[0][start.gathered_on.epoch()]
			print seconds
			median.append ( [(seconds +3600+ block_seconds/2) * 1000,
					 (tot + (vertical_block_seconds/2))  * 1000] )
	if test == 'compare':
		label = fdate.strftime('%d, %B')
	else:
		label = "Median (%ss)" % block_seconds
	return {'data': median,'label':label, 'id':'median_%s' %  block_seconds };


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())