# Eventory
A script for writing interactive stories
## Format v1
### meta
Information concerning 
- `version` A whole, non-negative number representing the current version of your Eventory
- `title`
- `description`
- `author`
- `pyrequirements` A list of python packages required to run the Eventory
### settings
Settings...
- `store` A mapping of custom variables which may be accessed inside the Eventory
### content
A list of events in the Eventory. The simplest event is an Output which can come in the form of a string