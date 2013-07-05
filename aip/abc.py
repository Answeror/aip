#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import abc


class MetaWithFields(abc.ABCMeta):

    def __new__(meta, name, bases, attr):
        if 'FIELDS' in attr:
            fields = attr['FIELDS']
            for field in fields:
                if type(field) is tuple:
                    key = field[0]
                else:
                    key = field
                attr[key] = abc.abstractproperty(lambda self: None)
        return abc.ABCMeta.__new__(meta, name, bases, attr)
