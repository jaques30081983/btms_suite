#from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, TableStyle
#from reportlab.graphics.barcode import eanbc, qr, usps
#from reportlab.graphics.shapes import Drawing
#from reportlab.graphics import renderPDF
from reportlab.platypus.tables import Table
#from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def eventDayResult(result):
	c = canvas.Canvas("spool/report.pdf")
	c.setPageSize((21*cm, 29.7*cm))
	page = 1
	
	
	def header_1(page, page_day):
		#Header 100 Range Cat II, III
		c.drawString(1*cm,28.5*cm, event_title)
		c.drawString(1*cm,28*cm,event_date_start +' - '+ event_date_end)

		c.drawString(12*cm,28.5*cm, date_day_name +' '+ row['date_day'])
		c.drawString(12*cm,28*cm, row['start_times'] + ', Page '+ str(page_day))
		c.drawString(17*cm,28.5*cm,"Total Page "+str(page))

		c.line(1*cm,27.5*cm,20*cm,27.5*cm)
		

	def body_1(start, end):
		#Body
		data= [['No.', 'Name', 'Cat II', 'Cat III']]
		
		for i in range(start,end):
			#Generate Transaction Id
			transaction_id = str(event_id)+event_date+event_time+str(i)
			transaction_id = filter(str.isalnum, str(transaction_id))

			luhn = generate(transaction_id)
			transaction_id = str(transaction_id)+luhn
			
			data.append([str(i)+','+luhn,'','','']) #####
			   

		tstyle = [('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
				  ('BOX', (0,0), (-1,-1), 0.25, colors.black),]
			   
		t = Table(data, colWidths=(3*cm, 4*cm, 6*cm, 6*cm))
		t.setStyle(TableStyle(tstyle))
		t.wrapOn(c, 1*cm, 0*cm)
		t.drawOn(c, 1*cm, 1*cm)

		c.showPage()


	for row in result:
		print row['date_day'], row['start_times'], row['admission']
		event_date = row['date_day']
		event_time = row['start_times']

		date_day = dt.datetime.strptime(row['date_day'], "%Y-%m-%d")
		date_day_name = date_day.strftime("%a")
		
		page_day = 1
		
		range_start = 100
		range_end = 140
		for j in range(0,6):
			header_1(page,page_day)
			body_1(range_start,range_end)

			range_start = range_start + 40
			range_end = range_end + 40

			page = page + 1
			page_day = page_day + 1
		



		

		
		
		
	createPDF(c)

def createPDF(c):
	c.save()



