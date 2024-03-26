#!/usr/bin/env python3

"""
Summarize a webpage using the OpenAI chat completion API
"""

import argparse
import shutil
import sys
import textwrap

from openai import OpenAI, OpenAIError
from requests_html import HTMLSession
from pyppeteer.errors import TimeoutError as PyppeteerTimeoutError

from ansi_colors import AnsiColors


def configure(args) -> dict:
    """
    Import configuration

    Args:
        args: Command line arguments

    Returns:
        conf: Configuration
    """

    try:
        conf_values = {}
        with open('summurai.conf', encoding='utf-8') as f:
            for line in f:
                key, value = line.strip().split('=')
                conf_values[key] = value

    except FileNotFoundError:
        conf_values = {
            'openai_api_key': '',
            'openai_chat_model': '',
        }

    conf = {
        'openai_api_key': args.api_key if args.api_key else conf_values['openai_api_key'],
        'openai_chat_model': args.model if args.model else conf_values['openai_chat_model'],
    }

    if conf['openai_api_key'] == '':
        print(
            'You must provide an OpenAI API key, using the --api-key option or by setting the '
            'openai_api_key value in the summurai.conf file.'
        )
        exit(1)

    if conf['openai_chat_model'] == '':
        conf['openai_chat_model'] = 'gpt-4-turbo-preview'

    return conf


def get_webpage(url: str) -> str:
    """
    Get webpage content from the URL
    
    Args:
        url: Webpage URL
        
    Returns:
        webpage_content: Webpage content
    """

    print('Retrieving webpage content...', file=sys.stderr)

    session = HTMLSession()
    response = session.get(url)

    try:
        response.html.render(timeout=10)

    except PyppeteerTimeoutError:
        pass

    session.close()

    webpage_title = ''
    for h1 in response.html.find('h1'):
        if h1.text.strip() != '':
            webpage_title = h1.text
            break

    webpage_paragraphs = ''
    for p in response.html.find('p'):
        if p.text.strip() != '':
            webpage_paragraphs += p.text + '\n\n'

    if webpage_paragraphs.strip() == '':
        if 'captcha' in response.html.html.lower():
            print('Could not retrieve webpage. It appears to use a CAPTCHA.', file=sys.stderr)
            exit(1)

        else:
            print('Could not retrieve webpage. Is there a paywall?', file=sys.stderr)
            exit(1)

    webpage_content = webpage_title + '\n\n' + webpage_paragraphs

    return webpage_content


def interactive_mode(prompt_messages: dict, conf: dict) -> None:
    """
    Interactive mode allows for further questions to be asked of the chat model regarding the
    article.

    Args:
        prompt_messages: Prompt message history
        conf: Configuration
    """

    openai = OpenAI(
        api_key=conf['openai_api_key'],
        max_retries=3,
        timeout=60,
    )

    print(
        f'\n__\n{AnsiColors.yellow}Interactive mode. Type "exit" to quit.{AnsiColors.reset}',
        file=sys.stderr,
    )

    while True:
        try:
            user_input = input(f'{AnsiColors.bold}You: ')
            if user_input.lower() == 'exit':
                break

        except EOFError:
            # Debug exit, prints prompt message history
            sys.exit(1)

        prompt_messages.append({
            'role': 'user',
            'content': user_input,
        })

        try:
            response = openai.chat.completions.create(
                model=conf['openai_chat_model'],
                messages=prompt_messages,
            )

            prompt_messages.append({
                'role': 'assistant',
                'content': response.choices[0].message.content,
            })

        except OpenAIError as e:
            print(f'OpenAI error: {e}')
            exit(1)

        print_wrapped(
            f'{AnsiColors.bold}{AnsiColors.cyan}summurai: '
            f'{AnsiColors.reset}{response.choices[0].message.content}\n'
        )


def parse_args():
    """
    Parse command line arguments

    Returns:
        args: command line arguments
    """

    parser = argparse.ArgumentParser(
        description='Summarize a webpage using the OpenAI chat completion API',
    )
    parser.add_argument(
        'url',
        type=str,
        help='URL of the webpage to summarize',
    )
    parser.add_argument(
        '-a', '--api-key',
        type=str,
        help='OpenAI API key',
    )
    parser.add_argument(
        '-m', '--model',
        type=str,
        help='Chat model to use for summarization',
    )
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Interactive mode',
    )

    args = parser.parse_args()
    return args


def print_wrapped(text: str) -> None:
    """
    Print text wrapped to the terminal width

    Args:
        text: Text to print
    """

    width = shutil.get_terminal_size().columns
    for line in text.split('\n'):
        print(textwrap.fill(line, width=width))


def summarize_webpage(webpage_content, conf):
    """
    Summarize the webpage content using the OpenAI chat completion API

    Args:
        webpage_content: Webpage content
        conf: Configuration

    Returns:
        summary: Summary of the webpage
        prompt_messages: Prompt message history
    """

    print('Summarizing webpage...', file=sys.stderr)

    openai = OpenAI(
        api_key=conf['openai_api_key'],
        max_retries=3,
        timeout=60,
    )

    prompt_messages = [{
        'role': 'system',
        'content': (
            'Produce a summary of the following article. Sections should include the article '
            'headline, a brief summary of the article, and a bulleted list of 3-4 key points. '
            'Following the summary, include an "in closing" section that includes some '
            'afterthoughts on the content of the article, including sentiment and its impact on '
            'society. Do not prompt the user for any additional information.'
            'IMPORTANT: After summarizing the article, return to a conversational tone. Provide '
            'SHORT and SIMPLE responses to questions.'
        ),
    },
    {
        'role': 'user',
        'content': webpage_content,
    }]

    try:
        response = openai.chat.completions.create(
            model=conf['openai_chat_model'],
            messages=prompt_messages,
        )

    except OpenAIError as e:
        print(f'OpenAI error: {e}')
        exit(1)

    summary = response.choices[0].message.content
    prompt_messages.append({
        'role': 'assistant',
        'content': summary,
    })

    return summary, prompt_messages


def main():
    """
    Main function
    """

    args                            = parse_args()
    conf                            = configure(args)
    webpage_content                 = get_webpage(args.url)
    summary, prompt_messages        = summarize_webpage(webpage_content, conf)
    print_wrapped(summary)

    if args.interactive:
        interactive_mode(prompt_messages, conf)

    print(
        f'{AnsiColors.reset}\n__\n'
        f'Generated by summurai -- https://github.com/jlyons210/summurai\n'
        f'Webpage URL: {args.url}\n'
        f'Summarized using: {conf["openai_chat_model"]}'
    )


if __name__ == '__main__':
    main()
