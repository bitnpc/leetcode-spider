#!/usr/bin/python
# coding:utf-8

import os
import json
import bs4
import requests

USER_AGENT = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'

class Spider(object):
    def __init__(self, path):
        self.base_url = 'https://leetcode.com/'
        self.path = path
        self.session = requests.Session()
    
    def login(self, username, password):
        url = self.base_url
        cookies = self.session.get(url).cookies
        for cookie in cookies:
            if cookie.name == 'csrftoken':
                csrftoken = cookie.value
        
        url = url + 'accounts/login'
        headers = {
            'User-Agent': USER_AGENT,
            'Connection': 'keep-alive',
            'Referer': 'https://leetcode.com/accounts/login/',
            "origin": "https://leetcode.com",
            'Content-Type': 'application/json'
        }
        param_data = {
            'csrfmiddlewaretoken': csrftoken,
            'login': username,
            'password': password,
            'next': 'problems'
        }
        self.session.post(url, headers=headers, data=param_data, timeout=10, allow_redirects = False)
        is_login = self.session.cookies.get('LEETCODE_SESSION') != None
        return is_login

    
    def get_problems(self):
        url = self.base_url + 'api/problems/algorithms'
        html = requests.get(url).content
        soup = bs4.BeautifulSoup(html, 'html.parser')
        problem_str = soup.prettify()
        problem_dic = json.loads(problem_str)
        problem_list = problem_dic['stat_status_pairs']

        max_cnt = 10
        i = 0
        for problem in reversed(problem_list):
            if i >= max_cnt:
                break
            i += 1
            if problem['paid_only']:
                continue
            self.get_problem_by_slug(problem['stat']['question__title_slug'])

    def get_problem_by_slug(self, slug):
        url = self.base_url + 'graphql'
        params = {
            'operationName': "getQuestionDetail",
            'variables': {'titleSlug': slug},
            'query': '''query getQuestionDetail($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    questionId
                    questionFrontendId
                    questionTitle
                    questionTitleSlug
                    content
                    difficulty
                    stats
                    similarQuestions
                    categoryTitle
                    topicTags {
                            name
                            slug
                    }
                }
            }'''
        }
        json_data = json.dumps(params).encode('utf8')
        headers = {
            'User-Agent': USER_AGENT, 
            'Connection': 'keep-alive', 
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problems/' + slug
        }
        resp = self.session.post(url, data=json_data, headers=headers, timeout=10)
        content = resp.json()

        question = content['data']['question']
        self.generate_problem_markdown(question)

    def generate_problem_markdown(self, question):
        save_path = os.path.join(self.path, "{:0>3d}-{}".format(int(question['questionFrontendId']), question['questionTitleSlug']))
        if not os.path.isdir(save_path):
            os.mkdir(save_path)
        with open(os.path.join(save_path, 'README.md'), 'w', encoding='utf-8') as f:
            f.write('## {}. {}'.format(question['questionFrontendId'], question['questionTitle']))

    def run(self):
        self.get_problems()

