import os
import random
import json
import string
import requests
import httplib2
import datetime

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from flask import Flask, render_template, request, redirect
from flask import session as login_session, url_for, flash, make_response
from werkzeug import secure_filename
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

import musicbrainzngs

from database_setup import Base, Users, Releases

app = Flask(__name__)

# CLIENT_ID = json.loads(
    # open('client_secret.json', 'r').read())['web']['client_id']

app.secret_key = 'super_secret_key'

musicbrainzngs.set_useragent(
    "mmellis-music-library",
    "0.1",
    "",
)
    
engine = create_engine('sqlite:///gifts.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def getUserID(email):
    try:
        user = session.query(Users).filter_by(email=email).one()
        return user.id
    except:
        return None


def releaseInfo(searchResults):
    allRealeases = []
    for result in searchResults:
        relInfo = {'artist': '', 'title': '', 'date': '', 
              'label-info-list': '', 'label': '', 'catalog-number': '', 
              'medium-list': '', 'format': '', 'barcode': ''}
        relInfo['artist'] = result['artist-credit-phrase']
        relInfo['title'] = result['title']
        if 'date' in result:
            relInfo['date'] = result['date']
        if 'label-info-list' in result:
            relInfo['label-info-list'] = result['label-info-list']
            relInfo['label'] = result['label-info-list'][0]['label']['name']
            if 'catalog-number' in result['label-info-list'][0]:
                relInfo['catalog-number'] = result['label-info-list'][0]\
                      ['catalog-number']
        if 'medium-list' in result:
            relInfo['medium-list'] = result['medium-list']
            relInfo['format'] = result['medium-list'][1]['format']
        if 'barcode' in result:
            relInfo['barcode'] = result['barcode']
        allRealeases.append(relInfo)
    return allRealeases


@app.route('/')
def index():
    return 'here it is'
    
    
@app.route('/artist_search/<string:artist>', methods=['GET','POST'])
def artistSearch(artist):
    result = musicbrainzngs.search_releases(artist=artist, limit=5)
    if not result['release-list']:
        return 'no results'
    # relList = result['release-list']
    relList = releaseInfo(result['release-list'])
    
    return render_template('release_results.html', releases=relList)
    


@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
        for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        # return credentials.access_token
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
            % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('\
            Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['gplus_id'] = gplus_id
    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['access_token'] = access_token
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user email exists, if it doesn't reject the login
    user_id = getUserID(data["email"])
    if not user_id:
        response = make_response(
            json.dumps("Email address not found."), 401)
        print "Email address not found."
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += ' -webkit-border-radius: 150px;-moz-border-radius: 150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output
    
    
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['access_token']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # invalid token
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    # only if signed in with Google Plus
    if not login_session.get('gplus_id') is None:
        gdisconnect()
    return redirect('/')


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
