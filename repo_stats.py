#!/usr/bin/env python3
"""Get Repo stats"""
import argparse
import csv
from collections import defaultdict as dd
import json
import os.path

MAX_PR = 18000
GH_META_DIR = "../bitcoin-gh-meta"
BITCOIN_DIR = "../bitcoin"
DESIRED_COMPONENTS = ['Build system',
                      'Config',
                      'Consensus',
                      'Descriptors',
                      'Docs',
                      'GUI',
                      'Logging',
                      'Mempool',
                      'Mining',
                      'Net processing',
                      'P2P',
                      'Policy',
                      'PSBT',
                      'Resource usage',
                      'RPC/REST/ZMQ',
                      'Scripts and tools',
                      'Tests',
                      'TX fees and policy',
                      'Utils/log/libs',
                      'UTXO Db and Indexes',
                      'Validation',
                      'Wallet']

pr_comments = {}

def print_comment_stats():
    with open("comments_stats.csv", "w") as stats_file:
        fieldnames = ['number', 'author', 'date']
        writer = csv.DictWriter(stats_file, fieldnames=fieldnames)
        writer.writeheader()

        for number in range(MAX_PR):

            path = "{}/issues/{}xx/{}-comments.json".format(GH_META_DIR, number // 100, number)
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                j = json.load(f)

            pr_comments[number] = len(j)

            for comment in j:
                if comment['user'] is not None:
                    writer.writerow({'number': str(number),
                                     'author': comment['user']['login'],
                                     'date': comment['created_at']})

def print_pr_stats():
    with open("pr_stats.csv", "w") as stats_file:
        fieldnames = ['number', 'author', 'opened', 'commits', 'comments', 'labels', 'state', 'closed']
        writer = csv.DictWriter(stats_file, fieldnames=fieldnames)
        writer.writeheader()
        for number in range(MAX_PR):

            path = "{}/issues/{}xx/{}-PR.json".format(GH_META_DIR, number // 100, number)
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                j = json.load(f)

            if 'labels' in j:
                labels = ';'.join([l['name'] for l in j['labels']])
            else:
                labels = ""

            writer.writerow({'number': str(number),
                             'author': j['user']['login'],
                             'opened': j['created_at'],
                             'commits': str(j['commits']),
                             'comments': (str(pr_comments[number]) if number in pr_comments else '0'),
                             'labels': labels,
                             'state': ("merged" if j['merged'] else j['state']),
                             'closed': (j['closed_at'] if j['state'] == 'closed' else "")})

def print_contributor_stats(contributor, year):
    print("Contributor {}".format(contributor))

    prs_opened = []
    labels_opened = dd(int)
    prs_merged = []
    prs_closed = []

    with open("pr_stats.csv", "r") as f:
        reader = csv.DictReader(f)
        for pr in reader:
            if pr['author'] == contributor:
                if int(pr['opened'][0:4]) == year:
                    prs_opened.append(pr)
                    for label in pr['labels'].split(';'):
                        if label in DESIRED_COMPONENTS:
                            labels_opened[label] += 1
                if pr['state'] == 'merged' and int(pr['closed'][0:4]) == year:
                    prs_merged.append(pr)
                if pr['state'] == 'closed' and int(pr['closed'][0:4]) == year:
                    prs_closed.append(pr)

    labels_ordered = [l for l in labels_opened.items()]
    labels_ordered.sort(key=lambda i: i[1], reverse = True)

    comments = []

    with open("comments_stats.csv", "r") as f:
        reader = csv.DictReader(f)
        for pr in reader:
            if pr['author'] == contributor:
                if int(pr['date'][0:4]) == year:
                    comments.append(pr)

    print("In {}:".format(year))
    print("You opened {} PRs".format(len(prs_opened)))
    print("Your favorite components were {}".format([l[0] for l in labels_ordered[0:3]]))
    print("You had {} PRs merged".format(len(prs_merged)))
    print("Your most popular PRs (by review comments) were {}".format([pr['number'] for pr in sorted(prs_merged, key=lambda i: int(i['comments']), reverse=True)[0:3]]))
    print("You made {} review comments".format(len(comments)))
    import pdb; pdb.set_trace()

def main():
    parser = argparse.ArgumentParser(add_help=False,
                                     usage='%(prog)s [test_runner.py options] [script options] [scripts]',
                                     description=__doc__)
    parser.add_argument('--build_stats', '-b', action='store_true', default=False, help="Create the stats files")
    parser.add_argument('--contributor', '-c', help="Specify which contributor to create stats for")
    parser.add_argument('--year', '-y', type=int, default=2019, help="Which year to create stats for")

    args, unknown_args = parser.parse_known_args()

    if args.build_stats:
        print_comment_stats()
        print_pr_stats()
    else:
        assert args.contributor, "You must specify a contributor"
        print_contributor_stats(args.contributor, args.year)

if __name__ == '__main__':
    main()
