#!/usr/bin/env python3
from xdg import BaseDirectory
import configparser
import requests
import subprocess
import sys
import webbrowser


class Confluence:
    def __init__(self, url, auth):
        self.url = url
        self.auth = auth

    def fetch(self, limit=500, start=0):
        confluence = requests.get(
            f'{self.url}/rest/api/search',
            params={
                'cql': 'type = page ORDER BY lastmodified DESC',
                'limit': limit,
                'start': start,
            },
            headers={'Content-Type': 'application/json'},
            auth=self.auth)
        pages = confluence.json()['results']
        for page in pages:
            space = page['resultGlobalContainer']['title']
            title = page['title']
            url = page['url'].strip("/")
            page['url'] = f'{self.url}/{url}'
            page['label'] = f'[{space}] {title}'
        return pages


class Jira:
    def __init__(self, url, auth):
        self.url = url
        self.auth = auth

    def fetch(self, limit=1000, start=0):
        jira = requests.get(
            f'{self.url}/rest/api/3/search',
            params={
                'jql': 'projectType = software ORDER BY updated DESC',
                'fields': 'summary',
                'maxResults': limit,
                'startAt': start,
            },
            headers={'Content-Type': 'application/json'},
            auth=self.auth)
        issues = jira.json()['issues']
        for issue in issues:
            key = issue['key']
            summary = issue['fields']['summary']
            issue['url'] = f'{self.url}/browse/{key}'
            issue['label'] = f'[{key}] {summary}'
        return issues


class Rofi:
    @classmethod
    def show_menu(cls, items, prompt):
        rofi_input = '\n'.join(items)
        rofi = subprocess.run(
            ['rofi', '-dmenu', '-p', prompt, '-format', 'i', '-i'],
            input=rofi_input,
            stdout=subprocess.PIPE,
            universal_newlines=True)
        rofi_key = rofi.returncode
        if rofi_key >= 0:
            try:
                return int(rofi.stdout)
            except:
                return None
        else:
            return None


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(BaseDirectory.load_config_paths('rofi-confluence-jira.cfg'))
    if len(sys.argv) > 1 and sys.argv[1] == 'confluence':
        confluence = Confluence(config['confluence']['URL'],
                                (config['confluence']['USER'], config['confluence']['PASS']))
        items = confluence.fetch(limit=500, start=0)
    else:
        jira = Jira(config['jira']['URL'],
                    (config['jira']['USER'], config['jira']['PASS']))
        items = jira.fetch(limit=1000, start=0)

    index = Rofi.show_menu([i['label'] for i in items], 'Confluence/JIRA')
    if index is not None:
        webbrowser.open_new_tab(items[index]['url'])
