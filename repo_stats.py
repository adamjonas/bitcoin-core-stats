#!/usr/bin/env python3
"""Get Repo stats"""
import argparse
import csv
from collections import defaultdict as dd
import datetime
import itertools
import json
import sys
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

def get_stats():
    comments_file = open("comments_stats.csv", "w")
    comments_fieldnames = ['number', 'author', 'date']
    comments_writer = csv.DictWriter(comments_file, fieldnames=comments_fieldnames)
    comments_writer.writeheader()

    reviewers_file = open("reviewer_stats.csv", "w")
    reviewers_fieldnames = ['reviewer', 'number', 'first_comment']
    reviewers_writer = csv.DictWriter(reviewers_file, fieldnames=reviewers_fieldnames)
    reviewers_writer.writeheader()

    reviewers = dd(int)
    first_comment = {}

    pr_file = open("pr_stats.csv", "w")
    pr_fieldnames = ['number', 'title', 'author', 'opened', 'commits', 'comments', 'labels', 'state', 'closed']
    pr_writer = csv.DictWriter(pr_file, fieldnames=pr_fieldnames)
    pr_writer.writeheader()

    authors_file = open("author_stats.csv", "w")
    authors_fieldnames = ['author', 'number_prs', 'number_commits', 'first_merge']
    authors_writer = csv.DictWriter(authors_file, fieldnames=authors_fieldnames)
    authors_writer.writeheader()

    authors = dd(int)
    authors_commits = dd(int)
    first_merge = {}

    for number in itertools.count():

        if not os.path.exists("{}/issues/{}xx".format(GH_META_DIR, number // 100)):
            break

        path = "{}/issues/{}xx/{}-comments.json".format(GH_META_DIR, number // 100, number)
        if not os.path.exists(path):
            continue
        with open(path, "r") as f:
            j = json.load(f)

        comments = 0
        for comment in j:
            comments += 1
            if comment['user'] is not None:
                user = comment['user']['login']
                comments_writer.writerow({'number': str(number),
                                          'author': user,
                                          'date': comment['created_at']})

                reviewers[user] += 1
                if user not in first_comment:
                    first_comment[user] = comment['created_at']
                else:
                    first_comment[user] = min(first_comment[user], comment['created_at'])

        path = "{}/issues/{}xx/{}-PR.json".format(GH_META_DIR, number // 100, number)
        if not os.path.exists(path):
            continue
        with open(path, "r") as f:
            j = json.load(f)

        if j['base']['label'] != "bitcoin:master":
            continue

        if 'labels' in j:
            labels = ';'.join([l['name'] for l in j['labels']])
        else:
            labels = ""

        author = j['user']['login']

        pr_writer.writerow({'number': str(number),
                            'author': author,
                            'title': j['title'],
                            'opened': j['created_at'],
                            'commits': str(j['commits']),
                            'comments': comments,
                            'labels': labels,
                            'state': ("merged" if j['merged'] else j['state']),
                            'closed': (j['closed_at'] if j['state'] == 'closed' else "")})

        if j['merged']:
            authors[author] += 1
            authors_commits[author] += j['commits']
            if author not in first_merge:
                first_merge[author] = j['created_at']
            else:
                first_merge[author] = min(first_merge[author], j['created_at'])

    for reviewer, number in reviewers.items():
        reviewers_writer.writerow({'reviewer': reviewer,
                                   'number': number,
                                   'first_comment': first_comment[reviewer]})

    for author, number in authors.items():
        authors_writer.writerow({'author': author,
                                 'number_prs': number,
                                 'number_commits': authors_commits[author],
                                 'first_merge': first_merge[author]})

def print_global_stats(year):
    prs_opened = []
    labels_opened = dd(int)
    prs_merged = []
    commits = 0
    prs_closed = []
    authors = set()

    with open("pr_stats.csv", "r") as f:
        reader = csv.DictReader(f)
        for pr in reader:
            if int(pr['opened'][0:4]) == year:
                prs_opened.append(pr)
                for label in pr['labels'].split(';'):
                    if label in DESIRED_COMPONENTS:
                        labels_opened[label] += 1
            if pr['state'] == 'merged' and int(pr['closed'][0:4]) == year:
                prs_merged.append(pr)
                commits += int(pr['commits'])
                authors.add(pr['author'])
            if pr['state'] == 'closed' and int(pr['closed'][0:4]) == year:
                prs_closed.append(pr)

    new_authors = 0
    with open("author_stats.csv", "r") as f:
        reader = csv.DictReader(f)
        for author in reader:
            if int(author['first_merge'][0:4]) == year:
                new_authors += 1

    labels_ordered = [l for l in labels_opened.items()]
    labels_ordered.sort(key=lambda i: i[1], reverse=True)

    comments = []
    commenters = set()

    with open("comments_stats.csv", "r") as f:
        reader = csv.DictReader(f)
        for comment in reader:
            if int(comment['date'][0:4]) == year:
                comments.append(comment)
                commenters.add(comment['author'])

    reviewers = 0
    new_reviewers = 0
    with open("reviewer_stats.csv", "r") as f:
        reader = csv.DictReader(f)
        for reviewer in reader:
            if int(reviewer['first_comment'][0:4]) == year:
                new_reviewers += 1
            if reviewer['reviewer'] in commenters and int(reviewer['number']) >= 5:
                reviewers += 1

    print("In {}...".format(year))
    print("{} PRs were opened".format(len(prs_opened)))
    print("The most active components were {}".format([l[0] for l in labels_ordered[0:5]]))
    print("{} PRs were merged with {} commits".format(len(prs_merged), commits))
    print("From {} unique authors ({} first time authors)".format(len(authors), new_authors))
    print("There were {} review comments".format(len(comments)))
    print("From {} unique regular* reviewers and {} first time reviewers".format(reviewers, new_reviewers))
    print("*A regular reviewer must have left >= 5 comments")

def get_contributor_stats(contributor, year):

    prs_opened = 0
    prs = []
    labels_opened = dd(int)
    prs_merged = 0
    prs_closed = 0
    commits = 0

    with open("pr_stats.csv", "r") as f:
        reader = csv.DictReader(f)
        for pr in reader:
            if pr['author'] == contributor:
                if int(pr['opened'][0:4]) == year:
                    prs_opened += 1
                    prs.append(pr)
                    for label in pr['labels'].split(';'):
                        if label in DESIRED_COMPONENTS:
                            labels_opened[label] += 1
                if pr['state'] == 'merged' and int(pr['closed'][0:4]) == year:
                    prs_merged += 1
                    if pr not in prs:
                        prs.append(pr)
                    commits += int(pr['commits'])
                if pr['state'] == 'closed' and int(pr['closed'][0:4]) == year:
                    prs_closed += 1
                    if pr not in prs:
                        prs.append(pr)

    labels_ordered = sorted([l for l in labels_opened.items()], key=lambda i: i[1], reverse=True)

    comments = 0

    with open("comments_stats.csv", "r") as f:
        reader = csv.DictReader(f)
        for comment in reader:
            if comment['author'] == contributor:
                if int(comment['date'][0:4]) == year:
                    comments += 1

    popular_prs = sorted(prs, key=lambda i: int(i['comments']), reverse=True)

    return {'year': year,
            'contributor': contributor,
            'prs_opened': prs_opened,
            'components': [(l[0], l[1]) for l in labels_ordered[0:3]],
            'prs_merged': prs_merged,
            'commits': commits,
            'popular_prs': popular_prs[0:3],
            'comments': comments}

def print_contributor_stats(all_stats, html):
    if not html:
        for contributor, stats_list in all_stats.items():
            print(f"Contributor {contributor}")
            for stats in stats_list:
                print(f"In {stats['year']}...")
                print("You opened {} PRs".format(stats['prs_opened']))
                print("Your favorite components were {}".format([c[0] for c in stats['components']]))
                print("You had {} PRs (including {} commits) merged".format(stats['prs_merged'], stats['commits']))
                print("Your most popular PRs (by review comments) were")
                for pr in stats['popular_prs']:
                    print(" - {}: {} ({} comments)".format(pr['number'], pr['title'], pr['comments']))
                print("You made {} review comments\n".format(stats['comments']))
    else:
        try:
            import jinja2
        except ImportError:
            print("jinja2 not found. Try `pip install jinja2`")
            sys.exit(1)
        print(jinja2.Environment(loader=jinja2.FileSystemLoader('./'))
              .get_template('stats_head.html')
              .render())
        for contributor, stats_list in all_stats.items():
            print(f"<h1>{contributor}</h1>")
            for stats in stats_list:
                print(jinja2.Environment(loader=jinja2.FileSystemLoader('./'))
                      .get_template('stats.html')
                      .render(stats=stats))
        print(jinja2.Environment(loader=jinja2.FileSystemLoader('./'))
              .get_template('stats_foot.html')
              .render())

def main():
    parser = argparse.ArgumentParser(add_help=False,
                                     description=__doc__)
    parser.add_argument('--build_stats', '-b', action='store_true', default=False, help="Create the stats files")
    parser.add_argument('--contributors', '-c', help="Specify which contributor to create stats for. You may pass multiple contributors separated by commas.")
    parser.add_argument('--globalstats', '-g', action='store_true', help="Print global stats")
    parser.add_argument('--help', '-?', action='store_true', help='print help text and exit')
    parser.add_argument('--html', '-h', action='store_true', help="Output HTML")

    year = str(datetime.date.today().year - 1)  # default to last year
    parser.add_argument('--years', '-y', default=year, help="Which years to create stats for (default {}). You may pass multiple years separated by commas.".format(year))

    args = parser.parse_args()

    if args.help:
        # Print help and exit.
        parser.print_help()
        sys.exit(0)

    if args.build_stats:
        get_stats()
    elif args.globalstats:
        print_global_stats(args.year)
    else:
        assert args.contributors, "You must specify a contributor"
        stats = {}
        contributors = args.contributors.split(',')
        years = [int(y) for y in args.years.split(',')]
        for contributor in contributors:
            stats[contributor] = []
            for year in years: 
                stats[contributor].append(get_contributor_stats(contributor, year))

        print_contributor_stats(stats, args.html)

if __name__ == '__main__':
    main()
