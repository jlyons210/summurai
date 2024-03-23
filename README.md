![summurai banner](./summurai_banner.png)

# summurai
Fetches and summarizes a webpage using OpenAI chat models.

## Demo
![screenshot](./summurai_demo.png)

## Usage
```sh
summurai.py [-h] [-a API_KEY] [-m MODEL] url

Summarize an article using the OpenAI chat completion API

positional arguments:
  url                   URL of the article to summarize

options:
  -h, --help            show this help message and exit
  -a API_KEY, --api-key API_KEY
                        OpenAI API key
  -m MODEL, --model MODEL
                        Chat model to use for summarization
```

## Setup
For convenience, the `summurai.conf` file allows you to configure the OpenAI API key and chat model to be used, so that they don't need to be provided on the command line. Command line arguments take precedence over configuration file values to allow easy overrides.


### Install dependencies
```sh
pip install -r requirements.txt
```

### Configure the application
> :bulb: Copy the configuration file template and add your API key using your favorite editor.
```sh
cp summurai.conf.template summurai.conf
```

### Have fun!
```sh
./summurai.py url_to_summarize
```
