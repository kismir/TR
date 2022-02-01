import sys
from PyQt5 import QtWidgets, QtCore 
from PyQt5.QtGui import QPainter, QColor
import random
from math import hypot

class CalcUtils():
    '''Functions to calculate intersection of rectangles in creation mode'''
    def __init__(self):
        pass

    def get_rectangle_we_clicked_on(self, rectangles, event):
        clicked_rectangle = None
        for rect in rectangles:
            dx = abs(rect.x+rect.w/2-event.pos().x())
            dy = abs(rect.y+rect.h/2-event.pos().y())
            if dx<(rect.w/2) and dy<(rect.h/2):
                clicked_rectangle = rect
                break
        return clicked_rectangle

    def check_if_rect_can_be_placed(self, rectangles, event):
        flag = 1
        for rect in rectangles:
            dx = abs(rect.x+rect.w/2-event.pos().x())
            dy = abs(rect.y+rect.h/2-event.pos().y())
            if dx<(rect.w) and dy<(rect.h):
                flag = 0
        return flag

    def check_rect_intersections_while_dragging_define_free_pos(self, rectangles, dragged_rect):
        intersected_rectangles = [rect for rect in rectangles if rect != dragged_rect]
        if len(intersected_rectangles)!=0:
            # represents all possible coordinate combinations in 2 lists: cx, cy
            cx, cy = [dragged_rect.x,], [dragged_rect.y,]
            for ir in intersected_rectangles:
                cx = cx + [ir.x - ir.w, ir.x + ir.w]
                cy = cy + [ir.y - ir.h, ir.y + ir.h]
            # check if possible coords are closest and consistent
            closest_coords = [cx[0], cy[0], float('inf')] 
            for x in cx:
                for y in cy:
                    flag = 1
                    for irect in intersected_rectangles:
                        dx = abs(irect.x-x)
                        dy = abs(irect.y-y)
                        if dx<(irect.w) and dy<(irect.h):
                            flag = 0
                    if flag == 1:
                        dst = hypot(x-dragged_rect.x, y-dragged_rect.y)
                        if dst<=closest_coords[2]:
                            # check if in new position does not overlap other rects
                            overlap_flag = 0
                            for rect in rectangles:
                                if rect != dragged_rect:
                                    dx = abs(rect.x-x)
                                    dy = abs(rect.y-y)
                                    if dx<(rect.w) and dy<(rect.h):
                                        overlap_flag = 1
                            if overlap_flag == 0:
                                closest_coords = [x,y,dst]
            dragged_rect.x = closest_coords[0]
            dragged_rect.y = closest_coords[1]

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        try:
            scr_geom_params = QtWidgets.QDesktopWidget().screenGeometry(-1)
            self.screen_h = scr_geom_params.height()
            self.screen_w = scr_geom_params.width()
        except:
            self.screen_h = 1920
            self.screen_w = 1080
        self.setGeometry(self.screen_w//6,self.screen_h//6,4*self.screen_w//6,4*self.screen_h//6)
        self.setWindowTitle('Tied Rectangles')
        self.selection_mode = 0
        self.dragged_rect = None
        self.dragged_rect_mouse_delta_pos_x = None
        self.dragged_rect_mouse_delta_pos_y = None
        self.group_handler = Groups()
        self.cu = CalcUtils()
        self.label_text = "Creation mode active. Tap 'SPACE' to enter selection mode."
        self.label = QtWidgets.QLabel(self.label_text, self)
        self.label.setFixedSize(700,150)
        self.label.move(50, 50)
        self.show()

    def get_lines_to_paint(self, gh):
        # list of lines that we gonna paint
        lines = []
        for gr in gh.groups:
            for line in list(gr.lines):
                lines.append(line)
        return lines

    def paintEvent(self, event):
        # here we paint all geometry
        qp = QPainter()
        qp.begin(self)
        for rect in self.group_handler.rectangles:        
            qp.setBrush(QColor(*rect.color))   
            qp.drawRect(rect.x, rect.y, rect.w, rect.h) 
        lines = self.get_lines_to_paint(self.group_handler)
        for line in lines:
            a,b = line.rectangles[0], line.rectangles[1]
            qp.drawLine(a.x+a.w/2, a.y+a.h/2, b.x+b.w/2, b.y+b.h/2)     
        qp.end()

    def mouseDoubleClickEvent(self, event):
        if self.selection_mode == 0:
            if event.button() == QtCore.Qt.LeftButton:
                # create new rectangle example
                if self.cu.check_if_rect_can_be_placed(self.group_handler.rectangles,event):
                    self.group_handler.rectangles.append(Rectangle(event))
                    self.update()
            else:
                pass

    def mouseMoveEvent(self, event):
        if self.selection_mode == 0:
            if event.buttons() == QtCore.Qt.LeftButton and self.dragged_rect != None:
                # change dragged rectangle coords
                self.dragged_rect.x = event.pos().x() - self.dragged_rect_mouse_delta_pos_x
                self.dragged_rect.y = event.pos().y() - self.dragged_rect_mouse_delta_pos_y
                # modify rectangle coords if intersections discovered
                self.cu.check_rect_intersections_while_dragging_define_free_pos(self.group_handler.rectangles, self.dragged_rect)
                self.update()

    def mousePressEvent(self, event):
        # work with objects mode
        if self.selection_mode == 0:
            if event.button() == QtCore.Qt.LeftButton:
                self.dragged_rect = self.cu.get_rectangle_we_clicked_on(self.group_handler.rectangles,event)
                if self.dragged_rect != None:
                    self.dragged_rect_mouse_delta_pos_x = event.pos().x() - self.dragged_rect.x
                    self.dragged_rect_mouse_delta_pos_y = event.pos().y() - self.dragged_rect.y
            else:
                pass
        # select objects mode
        elif self.selection_mode == 1:
            if event.button() == QtCore.Qt.LeftButton:
                sel_rect = self.cu.get_rectangle_we_clicked_on(self.group_handler.rectangles, event)
                if sel_rect != None:
                    self.group_handler.pass_rectangle_to_selected_to_unite_objects(sel_rect)
                self.update()
            if event.button() == QtCore.Qt.RightButton:
                sel_rect = self.cu.get_rectangle_we_clicked_on(self.group_handler.rectangles, event)
                if sel_rect != None:
                    self.group_handler.pass_rectangle_to_selected_to_untie_objects(sel_rect)
                self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            if self.selection_mode == 0:
                self.selection_mode = 1
                self.label_text = '''Selection mode active. Creation/movement disabled. Tap 'SPACE' to enter creation mode.
                - to add new connection leftclick on 2 rectangles consequentially;
                - to delete connection rightclick on 2 rectangles consequentially;'''
                self.label.setText(self.label_text)
            else:
                self.selection_mode = 0
                self.label_text = "Creation mode active. Tap 'SPACE' to enter selection mode."
                self.label.setText(self.label_text)
 
class Groups():
    '''Creates object, where all tied groups are held:
        - handles selected to unite rectangles
        - creates group based on selected to unite items
        - handles selected to untie rectangles
        - creates group based on selected to untie items'''
    def __init__(self):
        self.groups = []
        self.selected_rectangles_to_unite = []
        self.selected_rectangles_to_untie = []
        self.rectangles = []
 
    def create_group(self):
        a,b = self.selected_rectangles_to_unite
        if a!=b:
            if (a.group != None) and (b.group != None):
                if a.group != b.group: # rectangles are in different groups
                    #merge two groups (a.group,b.group) into a.group and clear b.group
                    a.group.rectangles = {**a.group.rectangles,**b.group.rectangles}
                    a.group.lines = {**a.group.lines,**b.group.lines}
                    # remember b.group, cause b.group will be change to a.group
                    bgroup = b.group 
                    # reassign group markers for rectangles and lines b -> a
                    for r in b.group.rectangles:
                        r.group = a.group
                    for l in b.group.lines:
                        l.group = a.group
                    a.group.tie_2_rectangles(a,b)
                    # remove group by reference variable bgroup
                    self.groups.remove(bgroup)
                else: # rectangles are in the same group
                    a.group.tie_2_rectangles(a,b)
            elif (a.group != None) and (b.group == None):
                a.group.tie_2_rectangles(a,b)
            elif (a.group == None) and (b.group != None):
                b.group.tie_2_rectangles(b,a)
            else:
                group = TiedGroup()
                group.tie_2_rectangles(a,b)
                self.groups.append(group)
 
    def a_b_has_far_connection(self,group,con_line,a,b):
        # breadth first search fast stop optimization on trees far connection check
        # Scheme of graph variant, we are worry about:   a--x--b   Scheme of cat: |\__/,|   (`\
        #                                                |     |                _.|o o  |_   ) )
        #                                                -->?<--               -<(<----<(<------                                                                                                 
        aqueue = []
        bqueue = []
        aqueue.append(a)
        bqueue.append(b)
        avisited = []
        bvisited = []
        avisited.append(a)
        bvisited.append(b)
        # start lines
        alines_start = [l for l in group.rectangles[a] if l != con_line]
        blines_start = [l for l in group.rectangles[b] if l != con_line]

        afront_nodes = [a,]
        bfront_nodes = [b,]
        circle_flag = 0

        arectangles = {}
        brectangles = {}
        alines = {}
        blines = {}
        while aqueue or bqueue:
            if len(aqueue) != 0:
                el = aqueue.pop()
                if el == a:
                    lines = alines_start
                else:
                    lines = list(group.rectangles[el])
                arectangles[el] = lines
                nodes = []
                for l in lines:
                    alines[l] = l.rectangles
                    rect = [rct for rct in l.rectangles if rct!=el][0]
                    nodes.append(rect)
                if len(set(afront_nodes) & set(bfront_nodes))!=0:
                    circle_flag = 1
                    break
                for node in nodes:
                    if node not in avisited:
                        aqueue.append(node)
                        avisited.append(node)            
                afront_nodes = nodes

            if len(bqueue) != 0:
                el = bqueue.pop()
                if el == b:
                    lines = blines_start
                else:
                    lines = list(group.rectangles[el])
                brectangles[el] = lines
                nodes = []
                for l in lines:
                    blines[l] = l.rectangles
                    rect = [rct for rct in l.rectangles if rct!=el][0]
                    nodes.append(rect)
                if len(set(afront_nodes) & set(bfront_nodes))!=0:
                    circle_flag = 1
                    break
                for node in nodes:
                    if node not in bvisited:
                        bqueue.append(node)
                        bvisited.append(node)
                bfront_nodes = nodes

        if circle_flag == 1:
            return True
        else:
            ga = TiedGroup()
            ga.rectangles = arectangles
            ga.lines = alines
            gb = TiedGroup()
            gb.rectangles = brectangles
            gb.lines = blines
            for r in ga.rectangles:
                r.group = ga
            for l in ga.lines:
                l.group = ga
            for r in gb.rectangles:
                r.group = gb
            for l in gb.lines:
                l.group = gb
            self.groups.remove(group)
            self.groups.append(ga)
            self.groups.append(gb)

            return False
 
    def separate_group_by_line(self,group,line):
        a,b = group.lines[line] # got rectangles that are connected by line
        if len(group.rectangles) == 2:
            group.untie_2_rectangles(line,a,b)
            self.groups.remove(group)
            a.group = None
            b.group = None
        elif len(a.group.rectangles[a])==1 and len(b.group.rectangles[b])>1:
            group.untie_2_rectangles(line,a,b)
            del group.rectangles[a] 
            a.group = None
        elif len(b.group.rectangles[b])==1 and len(a.group.rectangles[a])>1:
            group.untie_2_rectangles(line,a,b)
            del group.rectangles[b]
            b.group = None
        else:
            flag = self.a_b_has_far_connection(group,line,a,b) 
            if flag: # we've checked if there is circle path in node graph, that pass through our removing connection
                group.untie_2_rectangles(line,a,b)

    def pass_rectangle_to_selected_to_unite_objects(self,a):
        ''' pass rectangle to "selected to unite" objects and tries to create group'''
        self.selected_rectangles_to_unite.append(a)
        if len(self.selected_rectangles_to_unite) == 2:
            self.create_group()
            self.selected_rectangles_to_unite = []
 
    def check_if_rectangles_can_be_untied(self):
        a = self.selected_rectangles_to_untie[0]
        b = self.selected_rectangles_to_untie[1]
        if a!=b:
            if a.group != None and b.group!= None:
                line_list = list(set(a.group.rectangles[a]) & set(b.group.rectangles[b]))
                if len(line_list) == 0:
                    return False
                else:
                    return line_list[0]
            else:
                return False
            
        else:
            return False
 
    def pass_rectangle_to_selected_to_untie_objects(self,a):
        ''' pass rectangle to "selected to untie" objects and tries to create groups'''
        self.selected_rectangles_to_untie.append(a)
        if len(self.selected_rectangles_to_untie) == 2:
            tied_line = self.check_if_rectangles_can_be_untied()
            if tied_line:
                self.separate_group_by_line(tied_line.group,tied_line)

            self.selected_rectangles_to_untie = []
 
class TiedGroup():
    '''Creates tied group object, can:
        - tie 2 rectangles in group
        - simple untie of 2 rectangles'''
    def __init__(self):
        self.rectangles = dict()
        self.lines = dict()
 
    def tie_2_rectangles(self,a,b):
        a.group = self
        b.group = self
        line = Line(a,b)
        line.group = self
        self.lines[line] = (a,b)
        if a not in self.rectangles:
            self.rectangles[a] = [line,]
        else:
            self.rectangles[a].append(line)
        if b not in self.rectangles:
            self.rectangles[b] = [line,]
        else:
            self.rectangles[b].append(line)
 
    def untie_2_rectangles(self, line, a, b):
        # simple clean of lines and rectangles notes in group
        self.rectangles[a].remove(line)
        self.rectangles[b].remove(line)
        del self.lines[line]
 
class Rectangle():
    def __init__(self, event):
        self.group = None
        self.h = 100
        self.w = 200
        self.x = event.pos().x()-self.w/2
        self.y = event.pos().y()-self.h/2
        self.color = (random.randint(10,245), random.randint(10,245), random.randint(10,245))

class Line():
    def __init__(self,a,b):
        self.group = None
        self.rectangles = [a,b]

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWidget()
    window.show()
    sys.exit(app.exec_())
