#!/usr/bin/env python
# encoding: utf-8
"""
@author: wzq
@File    : word_filter.py
@desc    : 敏感词过滤
"""
from collections import defaultdict
import re
import os

# from config import base_path

# WordFilePath = os.path.join(base_path, 'utils/filter/wd.txt')
WordFilePath = './wd.txt'


class NaiveFilter():
    '''Filter Messages from keywords

    very simple filter implementation

    # >>> f = NaiveFilter()
    # >>> f.add("sexy")
    # >>> f.filter("hello sexy baby")
    hello **** baby
    '''

    def __init__(self):
        self.keywords = set([])

    def parse(self, path):
        for keyword in open(path):
            self.keywords.add(keyword.strip().decode('utf-8').lower())

    def word_replace(self, message, repl="*"):
        message = str(message).lower()
        for kw in self.keywords:
            message = message.replace(kw, repl)
        return message


class BSFilter:
    '''Filter Messages from keywords

    Use Back Sorted Mapping to reduce replacement times

    # >>> f = BSFilter()
    # >>> f.add("sexy")
    # >>> f.filter("hello sexy baby")
    hello **** baby
    '''

    def __init__(self):
        self.keywords = []
        self.kwsets = set([])
        self.bsdict = defaultdict(set)
        self.pat_en = re.compile(r'^[0-9a-zA-Z]+$')  # english phrase or not
        self.path = WordFilePath

    def add(self, keyword):
        if isinstance(keyword, bytes):
            keyword = keyword.decode('utf-8')
        keyword = keyword.lower()
        if keyword not in self.kwsets:
            self.keywords.append(keyword)
            self.kwsets.add(keyword)
            index = len(self.keywords) - 1
            for word in keyword.split():
                if self.pat_en.search(word):
                    self.bsdict[word].add(index)
                else:
                    for char in word:
                        self.bsdict[char].add(index)

    def parse(self):
        with open(self.path, "r", encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())

    def word_replace(self, message, repl="*"):
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        message = message.lower()
        for word in message.split():
            if self.pat_en.search(word):
                for index in self.bsdict[word]:
                    message = message.replace(self.keywords[index], repl)
            else:
                for char in word:
                    for index in self.bsdict[char]:
                        message = message.replace(self.keywords[index], repl)
        return message


class DFAFilter():
    '''Filter Messages from keywords

    Use DFA to keep algorithm perform constantly

    # >>> f = DFAFilter()
    # >>> f.add("sexy")
    # >>> f.filter("hello sexy baby")
    hello **** baby
    '''

    def __init__(self):
        self.keyword_chains = {}
        self.delimit = '\x00'
        self.path = WordFilePath

        # 初始化词库
        self.parse()

    def add(self, keyword):
        if isinstance(keyword, bytes):
            keyword = keyword.decode('utf-8')
        keyword = keyword.lower()
        chars = keyword.strip()
        if not chars:
            return
        level = self.keyword_chains
        for i in range(len(chars)):
            if chars[i] in level:
                level = level[chars[i]]
            else:
                if not isinstance(level, dict):
                    break
                for j in range(i, len(chars)):
                    level[chars[j]] = {}
                    last_level, last_char = level, chars[j]
                    level = level[chars[j]]
                last_level[last_char] = {self.delimit: 0}
                break
        if i == len(chars) - 1:
            level[self.delimit] = 0

    def parse(self):
        with open(self.path, encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())

    def word_replace(self, message, repl="*"):
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        message = message.lower()
        ret = []
        start = 0
        while start < len(message):
            level = self.keyword_chains
            step_ins = 0
            for char in message[start:]:
                if char in level:
                    step_ins += 1
                    if self.delimit not in level[char]:
                        level = level[char]
                    else:
                        ret.append(repl * step_ins)
                        start += step_ins - 1
                        break
                else:
                    ret.append(message[start])
                    break
            else:
                ret.append(message[start])
            start += 1

        return ''.join(ret)


if __name__ == '__main__':
    print('start')
    f = DFAFilter()
    f.add("sexy")
    # f.filter("hello sexy baby")
    print(f.word_replace("hello sexy baby"))
    gfw = DFAFilter()
    gfw.add('XINGFU')
    print(gfw.word_replace('什么是XINGFU騷棒文化大革命', "*"))
    print(gfw.word_replace("传世私服 我操操操", "*"))

    # gfw = BSFilter()
    # gfw.add("操")
    # print(gfw.word_replace("传世私服 我操操操", "*"))
