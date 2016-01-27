from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.graphics.barcode import eanbc, qr, usps
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF


def createPdfTicket(self,result):
    event_id = '0'
    event_date = '0'
    event_time = '0'
    item_id = '0'
    cat_id = '0'
    art = '0'
    amount = '0'

    seats = '0'
    status = '0'
    user_id = '0'
    c = canvas.Canvas('../spool/ticket_'+ result[0]['tid'] +'.pdf')
    c.setPageSize((8*cm, 16*cm))
    for row in result:


        #c.drawImage("company_logo_01.png", 1*cm, 9*cm,6*cm,6*cm)
        c.line(1*cm,8.7*cm,7*cm,8.7*cm)

        c.drawString(1*cm,8*cm, row['date']+','+ row['time'] +'Uhr')
        c.drawString(1*cm,7.5*cm,"Zentraler Festplatz")
        c.drawString(1*cm,7.0*cm,"Kurt-Schumacher-Damm 207")
        c.drawString(1*cm,6.5*cm,"DE 13405 Berlin")

        c.line(1*cm,6.3*cm,7*cm,6.3*cm)

        c.drawString(1*cm,5.5*cm,"Kategorie: Loge - Kat 1")
        c.drawString(1*cm,5*cm,'Block: Loge '+ row['item_id'] +', Sitz: '+ row['seat'])

        c.line(1*cm,4.5*cm,7*cm,4.5*cm)

        c.drawString(1*cm,3.7*cm,"Norm. ")
        c.drawString(1*cm,2.5*cm,"35,00 EUR")

        #c.drawString(1*cm,7.0*cm,"DE 13405 Berlin")
        # draw a QR code
        qr_code = qr.QrCodeWidget(str(row['tid'])+'_'+str(row['ticket_id']))
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        d = Drawing(45, 45, transform=[99./width,0,0,99./height,0,0])
        d.add(qr_code)
        renderPDF.draw(d, c, 4*cm, 1.1*cm)


        c.drawString(1*cm,1*cm,"TID: "+ row['tid'] + "_" + str(row['ticket_id']))

        c.showPage()

    c.save()
    return 'ticket created'



