# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import datetime
from ast import literal_eval
import os

lesson_type = {"lesson-color-type-1" : "📗",
               "lesson-color-type-2" : "📘",
               "lesson-color-type-3" : "📕",
               "lesson-color-type-4" : "📙"
               }

class Day(object):
    """Day object
    
    Args:
        :date: :class:`datetime.time` date date date date date date date date date
        :lessons: `list` of lessons
    """
    def __init__(self, date, lessons):
        self.date = date
        self.lessons = lessons

class Shedule(object):
    """Shedule object
    
    Args:
        groupID: `int` id of group in SSAU site
        group: `str` local number of group (e.g. 2205-240502D)
        week: (optional) `int` number of week of semester
    """
    def __init__(self, groupID, group, week=1):
        self.group = group
        self.groupID = groupID
        self.week = week
    
    def update(self, week = None, add_info = None):
        """Load shedule from SSAU and parse
        
        Args:
            week: `int` number of week of semester
            add_info Additional information about teacher (`dict` {"surname":"information"})
        """
        if week != None : self.week = week 
        site = requests.get(f'https://ssau.ru/rasp?groupId={self.groupID}&selectedWeek={self.week}')
        print(site)
        self.contents = site.text.replace("\n", " ")
        self.parse(add_info)
    
    def parse(self, add_info = None):
        """Parsing of SSAU Shedule page
        
        Args:
            add_info: Additional information about teacher (`dict` {"surname":"information"})     
        """

        self.add_info = add_info
        soup = BeautifulSoup(self.contents, 'html.parser')

        # parse schedule from site
        shedule_soup = soup.find("div", {"class": "schedule__items"}) 
        
        dates = self.get_dates(shedule_soup)        
        lessons = self.get_lessons(shedule_soup)
        
        for i, lesson in enumerate(lessons): 
            self.save(dates[i], lesson)
        
        self.timetable = self.get_times(shedule_soup)
        self.save_timetable(self.timetable)
                
    
    def get_dates(self, soup):
        """Find dates from the shedule soup (class "schedule__head-date")
        
        Args:
            soup: HTML soup of the shedule
        
        Returns:
            dates: `list` of :class:`datetime.date` objects 
        """
        dates_soup = soup.find_all("div", {"class": "schedule__head-date"})
        dates = []
        for d in dates_soup:
            date = [int(i) for i in d.text.split(".")]
            dates.append(datetime.date(date[2], date[1], date[0]))    
            
        return dates
    
    
    def get_times(self, soup):
        """Find times of lessons from the shedule soup (class "schedule__time")
        
        Args:
            soup: HTML soup of the shedule
        
        Returns:
            times: `list` of `tuples` of :class:`datetime.time` objects: (begin, end) 
        """    
        
        times_soup = soup.find_all("div", {"class": "schedule__time"})
        times = []
        for time in times_soup:
            _begin = [int(i) for i in time.contents[0].text.split(":")]
            begin = datetime.time(_begin[0], _begin[1])
            
            _end = [int(i) for i in time.contents[1].text.split(":")]
            end = datetime.time(_end[0], _end[1])   
            
            times.append((begin, end))

        return times 
    
    
    def get_lessons(self, soup):
        """Find lessons from the shedule soup (class "schedule__item" except "schedule__head")
        
        Args:
            soup: HTML soup of the shedule
        
        TODO: write returns
        """ 
        
        lessons_soup = soup.find_all("div", {"class": "schedule__item"})
        # delete "schedule__head" from soup
        lessons_soup = [item for item in lessons_soup if "schedule__head" not in item.attrs["class"]]
        
        lessons = []
        while lessons_soup != []:
            lesson = []
            for l in lessons_soup[:6]:
                sub_pairs = l.find_all("div", {"class": "schedule__lesson"})
                
                pair = []
                for sub_pair in sub_pairs:
                    if sub_pair != []:
                        name = sub_pair.find("div", {"class": "schedule__discipline"})
                        teacher = sub_pair.find("div", {"class": "schedule__teacher"}).text
                        place = sub_pair.find("div", {"class": "schedule__place"}).text
                        groups = sub_pair.find("div", {"class": "schedule__groups"}).text
                        comment = sub_pair.find("div", {"class": "schedule__comment"}).text
                                                    
                        # detect online lessons
                        if place.find("ON") != -1:
                            place = None                        
                        
                        lesson_name = lesson_type[name["class"][-1]] + name.text
                        
                        info = {}
                        info["lesson"] =  lesson_name
                        if teacher.replace(" ","") != "":
                            info["teacher"] = teacher
                            surname = teacher.split()[0]
                            if surname in self.add_info:
                                info["attachment"] = self.add_info[surname]
                                
                        if place != None: 
                            info["place"] = place
                        if groups.find("группы") != -1:
                            info["groups"] = groups
                        if comment != "":     
                            info["comment"] = comment
                        pair.append(info)
                        
                lesson.append(pair)
                
            lessons.append(lesson)        
            lessons_soup = lessons_soup[6:]
            
        days = [[] for i in range(6)]    
        for row in lessons:
            for day, pair in enumerate(row):
                days[day].append(pair)
                
        return days       
        
        
    
    def save_timetable(self, time):
        """Save timetable to file
        
        Args:
            time: timetable `tuple` ((begin, end) ...)   
        """
        
        if not os.path.isdir(f'shedules'):
            os.makedirs(f'shedules') 
        
        timetable = []    
        for i, t in enumerate(time):
            begin = (t[0].hour, t[0].minute)
            end = (t[1].hour, t[1].minute)
            timetable.append((begin, end))      
            
        path = os.path.abspath(f'shedules/timetable.json')        
        with open(path, 'w', encoding="utf-8") as f:
            f.write(str(timetable).replace(")), ", ")), \n"))
            
    def load_timetable(self):
        """Load timetable from file
        
        Returns: timetable `tuple` ((begin, end) ...)
        """
        path = os.path.abspath(f'shedules/timetable.json') 
        with open(path, 'r', encoding="utf-8") as f:        
            timetable = literal_eval(f.read())
            
            self.timetable = []
            for time in timetable:
                begin = datetime.time(time[0][0], time[0][1])
                end = datetime.time(time[1][0], time[1][1])
                self.timetable.append((begin, end))
        return self.timetable
    
    def save(self, date, lessons):
        """Save shedule to file
        
        Args:
            date: :class:`datetime.time` 
            lessons: `list` of lessons
        """
                
        day_str = f"{date.month}-{date.day}-{date.year}" 
        
        if not os.path.isdir(f'shedules/{self.group}/'):
            os.makedirs(f'shedules/{self.group}')
            
        path = os.path.abspath(f'shedules/{self.group}/shedule-{day_str}.json')        
        with open(path, 'w', encoding="utf-8") as f:
            f.write(str(lessons).replace("], ", "], \n"))
            
    def load(self, date):
        """Loading the schedule for a given day
        
        Args:
            date: :class:`datetime.date` object of day
            
        Returns:
            :class:`Day` object
        
        """
        day_str = f"{date.month}-{date.day}-{date.year}" 
        path = os.path.abspath(f'shedules/{self.group}/shedule-{day_str}.json')        
        with open(path, 'r', encoding="utf-8") as f:        
            lessons = literal_eval(f.read())       
        
        return Day(date, lessons) 
      
    def clear_old(self, date):
        """Clear all files before a given date
    
        Args:
           date: a :class:`datetime.date` object
        """
        path = os.path.abspath(f'shedules/{self.group}/')
        files = os.listdir(path)
        for file in files:
            day = file[:-5].split("-")[1:] 
            day = [int(i) for i in day]
            file_date = datetime.date(day[2], day[0], day[1])
            if file_date < date:
                os.remove(os.path.abspath(f'shedules/{self.group}/{file}'))
        
    
if __name__ == "__main__":
    delta = datetime.timedelta(hours=4, minutes=0)
    
    path = os.path.abspath('settings/extra.txt')
    with open(path, 'r', encoding="utf-8") as f:
        extra = literal_eval(f.read())
        
    sh = Shedule(530996164, 2205, 10)
    t = (datetime.datetime.now(datetime.timezone.utc) + delta)
    #t = datetime.datetime(2021, 10, 27, 11, 00, 00, 00)
    print(t.hour, t.minute, t.weekday())
    
    sh.clear_old(t.date())
    
    #sh.update(add_info = extra)
    #now_day = sh.load(t.date())
    
    #print(now_day.lessons)
            
