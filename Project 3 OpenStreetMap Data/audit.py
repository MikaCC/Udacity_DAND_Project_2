#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  8 23:26:19 2017

@author: sicongchen
"""

import lxml.etree as ET
from collections import defaultdict
import re
import pandas as pd


street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", "Way", "Trail", "Parkway", "Commons", "Circle", "Terrace", "Highway"]
            
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def audit_street(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                # if the tag is a street
                if tag.attrib['k'] == "addr:street":
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


mapping = { "St": "Street",
            "St.": "Street",
            "street": "Street",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard",
            "Boulavard": "Boulevard",
            "Rd": "Road",
            "Rd.": "Road",
            "RD": "Road",
            "Pl": "Place",
            "Pl.": "Place",
            "PKWY": "Parkway",
            "Pkwy": "Parkway",
            "parkway":"Parkway",
            "Ln": "Lane",
            "Ln.": "Lane",
            "Dr": "Drive",
            "Dr.": "Drive",
            "Plz": "Plaza",
            "Hwy": "Highway",
            "Ctr": "Center"
            }
            
# update street name according to the mapping dictionary
def fix_street(osmfile):
    st_types = audit_street(osmfile)
    for st_type, ways in st_types.iteritems():
        for name in ways:
            if st_type in mapping:
                better_name = name.replace(st_type, mapping[st_type])
                print name, "=>", better_name
                

def audit_city(filename):
    osm_file = open(filename, "r")  
    city_list = set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if tag.attrib['k'] == "addr:city" and tag.attrib['v'] != 'San Francisco':
                    city_list.add(tag.attrib['v'])
    return city_list
    
    


def audit_postcode(filename):
    osm_file = open(filename, "r")  
    code_list = set()
    long_code = 0
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if tag.attrib['k'] == "addr:postcode":
                    if len(tag.attrib['v']) > 5:
                        long_code += 1
                        
                        tag.attrib['v'] = tag.attrib['v'].split('-')[0]
                        code_list.add(tag.attrib['v'])
                                      
    print 'There are', long_code, 'long post codes.'
    return code_list  
                  

def audit_phone(filename):
    osm_file = open(filename, "r")  
    phone_list = []
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if (tag.attrib['k'] == "phone") or (tag.attrib['k'] == "contact:phone"):
                    phone_list.append(tag.attrib['v']) 
    return phone_list
 
# standard format: XXX-XXX-XXXX or 1-XXX-XXX-XXXX 
def fix_phone(phone):
    # first deal with strings with no separators
    if re.compile(r'^(\d{3})(\d{3})(\d{4})$').search(phone):
        # XXXXXXXXXX 
        return phone[:3] + '-' + phone[3:6] + '-' + phone[6:]
    elif re.compile(r'^1(\d{10})$').search(phone):           
       # 1XXXXXXXXXX
        return phone[1:4] + '-' + phone[4:7] + '-' + phone[7:]
    elif re.compile(r'^\+1(\d{10})$').search(phone):           
       # +1XXXXXXXXXX
        return phone[2:5] + '-' + phone[5:8] + '-' + phone[8:]
    elif re.compile(r'^\+1\s(\d{10})$').search(phone):           
       # +1 XXXXXXXXXX
        return phone[3:6] + '-' + phone[6:9] + '-' + phone[9:]
    elif re.compile(r'^\+1\s(\d{3})\s(\d{3})(\d{4})$').search(phone):
        # +1 XXX XXXXXXX
        return phone[3:6] + '-' + phone[7:10]+ '-' + phone[10:]
    elif re.compile(r'^01\s(\d{3})\s(\d{3})\s(\d{4})$').search(phone):
        # 01 XXX XXX XXXX 
        return phone[3:].replace(' ', '-')
    
    # if more than one number in the string, split to a list    
    elif phone.find(';') > 0:
        for ph in phone.split(';'):
            fix_phone(ph) 
            
    # if there are 3 or 4 digital parts, concatenate with dash 
    elif len(re.findall('\d+', phone)) >2:
        return '-'.join(re.findall('\d+', phone))
        
    else:
        print phone

 #use this function to loop up audit and fix for phone numbers  
def fix_phonenumber(filename):
    phone_list = audit_phone(filename)
    for phone in phone_list:
        fix_phone(phone)