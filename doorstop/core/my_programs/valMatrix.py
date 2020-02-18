# Create an html output of the validationMatrix

import os
from doorstop import common
from doorstop.common import DoorstopError
from doorstop.core.types import iter_documents, iter_items, is_tree, is_item
from doorstop import settings
from datetime import datetime

# Create path to css file for verification matrix
Matrix_Unchanged_CSS = os.path.join(os.path.dirname(__file__),'..', 'files', 'valMatrix.css')



log = common.logger(__name__)



def publish_Matrix(obj, path): 

    """Publish validation matrix as html file.

    :param obj: (1) Item, list of Items, Document or (2) Tree
    :param path: (1) output file path or (2) output directory path
    

    #:raises: :class:`doorstop.common.DoorstopError` for unknown file formats

    

    """
    # Set file output extension to html 
    extension = '.html'
    
    if  is_tree(obj):     
        for tmp_obj, tmp_path in iter_documents(obj, path, extension):       
            # Make file and write created lines into it
            common.create_dirname(tmp_path)      
            lines = _publish_lines(tmp_obj)
            common.write_lines(lines,tmp_path)

    else: 
        path = os.path.join(path, obj.prefix + extension)
        # Make file and write created lines into it
        common.create_dirname(path)  
        lines = _publish_lines(obj)
        common.write_lines(lines,path)
    
        


def _publish_lines(tmp_obj):
    ''' 
    Yield lines for an html validation Matrix

    param tmp_object: tree like object to publish 
    
    '''

    # Create html-files 
   
    yield '<!DOCTYPE html>'
    yield '<html lang="en">'
    yield '<head>'
    yield '<title>validation matrix</title>'

    yield '<style type="text/css">'
    yield from _lines_valMatrix_css() 
    yield '</style>'
    yield '</head>'

    yield '<body>'
    yield '<div class="background-color"></div>'
    yield '<div class="Center-align">'
    yield '<h1 >Validation Matrix</h1>'
    yield '</div>'

    # Print button
    yield '<button onclick="Print()">Print</button>'
    yield '<div class = "float-right"><strong>Hit "ctrl+s" to save changes!</strong></div>'

    yield '<table width=50% >'
    yield '<tbody>'

    yield '<tr>'
    yield '<td>Project</td>'
    # Project
    yield '<td contenteditable="true">'
    yield ''
    yield '</td>'
    yield '</tr>'

    yield '<tr>'
    yield '<td>Validation Matrix for</td>'
    # Name for document of validation
    yield '<td>'
    yield tmp_obj.prefix
    yield '</td>'
    yield '</tr>'

    yield '<tr>'
    yield '<td>Date</td>'
    # Date of creation  
    yield '<td>'
    yield datetime.today().strftime('%d/%m/%Y')
    yield '</td>'
    yield '</tr>'

    yield '<tr>'
    yield '<td>Owner</td>'
    # Owner 
    yield '<td contenteditable="true">'
    yield ''
    yield '</td>'
    yield '</tr>'

    yield '<tr>'
    yield '<td>Issue</td>'
    # Issue 
    yield '<td contenteditable="true">'
    yield ''
    yield '</td>'
    yield '</tr>'

    yield '</tbody>'
    yield '</table>'
    
    

    yield '<table width=100% >'
    yield '<tbody>'
    yield '<tr>'
    yield '<th colspan="2" width=20%>Requirements</th>'
    yield '<th colspan="4" width=40%>Traceabillity</th>'
    yield '<th colspan="4" width=40%>Validation</th>'
    yield '</tr>'

    yield '<tr>'
    yield '<th colspan="2" width=20%>Req. ID</th>'
    yield '<th colspan="2" width=20%>Parent req. ID</th>'
    yield '<th colspan="2" width=20%>Rationale</th>'
    yield '<th colspan="1" width=10%>Validation Method</th>'
    yield '<th colspan="2" width=20%>Validation evidence Method</th>'
    yield '<th colspan="1" width=10%>Conclusion</th>'
    yield '</tr>'
    
    
    for item in tmp_obj:
        if item.Is_Req:
            yield '<tr>'

            # Write values in Req.ID
            yield '<td colspan="2" width=20% contenteditable="false">'
            yield str(item.uid)
            yield '</td>'

            # Write value for parent req. ID
            yield '<td colspan="2" width=20% contenteditable="false">'
            if not len(item.links) == 0:
                for link in item.links:
                    yield str(link) + '<br>'
            else:
                yield ''
            yield '</td>'

            # Write rationale
            yield '<td colspan="2" width=20% contenteditable="fasle">'
            yield str(item.SPEC_RATIONALE) 
            yield '</td>'

            # Write value for Validation Method 
            yield '<td colspan="1" width=10% contenteditable="true">'
            yield '<div class="Center-align">'
            yield str(item.Validation_Mean)
            yield '</div>'
            yield '</td>'


            # Write validation evidence reference 
            yield '<td colspan="2" width=20% contenteditable="true">'
            yield ''  # Manul user entry 
            yield '</td>'

            # Write status/conclusion of requirement
            yield '<td colspan="1" width=20% contenteditable="true">'
            yield '<div class="Center-align">'
            yield str(item.SPEC_STATUS)
            yield '</div>'
            yield '</td>'

            yield '</tr>'

    yield '</tbody>'
    yield '</tabele>'

    # Function for the Print Button
    yield '<script>function Print() {window.print();}</script>'
    yield '<script>function Safe() {window.safe();}</script>'

    yield '</body>'
    yield '</html>'


def _lines_valMatrix_css():
    yield ''
    for line in common.read_lines(Matrix_Unchanged_CSS):
        yield line.rstrip()
    yield ''
