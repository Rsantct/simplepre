/*
Copyright (c) 2019 Rafael Sánchez
This file is part of 'simplepre' which is
based on FIRtro https://github.com/AudioHumLab/FIRtro
Copyright (c) 2006-2011 Roberto Ripio
Copyright (c) 2011-2016 Alberto Miguélez
Copyright (c) 2016-2018 Rafael Sánchez
'simplepre' is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
pre.di.c is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with 'simplepre'.  If not, see https://www.gnu.org/licenses/.
*/

/*
   debug trick: console.log(something);
   NOTICE: remember do not leaving any console.log actives
*/

/* TO REVIEW: At some http request we use sync=false, this is not recommended
              but this way we get the answer.
              Maybe it is better to use onreadystatechange as per in refresh_predic_status()
*/

/////////////   GLOBALS //////////////
auto_update_interval = 1500;                // Auto-update interval millisec


// Used from buttons to send commands to pre.di.c
function control_cmd(cmd, update=true) {
    // Sends the command to pre.di.c through by the server's PHP:
    // https://www.w3schools.com/js/js_ajax_http.asp
    var myREQ = new XMLHttpRequest();
    myREQ.open("GET", "php/functions.php?command=" +  cmd, true);
    myREQ.send();

    // Then update the web page
    if (update) {
        refresh_predic_status();
    }
}

//////// PAGE MANAGEMENT ////////

// Initializaes the page, then starts the auto-update
function page_initiate() {

    // Web header shows the loudspeaker name
    document.getElementById("main_center").innerText = ':: ' + get_loudspeaker_name() + ' ::';

    // Queries the pre.di.c status and updates the page
    refresh_predic_status();
        
    // Waits 1 sec, then schedules the auto-update itself:
    // Notice: the function call inside setInterval uses NO brackets)
    setTimeout( setInterval( refresh_predic_status, auto_update_interval ), 1000);
}

// Gets the pre.di.c status and updates the page
function refresh_predic_status() {
    // https://www.w3schools.com/js/js_ajax_http.asp

    var myREQ = new XMLHttpRequest();

    // Will trigger an action when HttpRequest has completed: page_update
    myREQ.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            page_update(this.responseText);
        }
    };

    // the http request:
    myREQ.open(method="GET", url="php/functions.php?command=status", async=true);
    myREQ.send();
}

// Dumps pre.di.c status into the web page
function page_update(status) {

    // Level, balance, tone info
    document.getElementById("levelInfo").innerHTML  = 'LEV: '  + status_decode(status, 'level');
    document.getElementById("bassInfo").innerText   = 'BASS: ' + status_decode(status, 'bass');
    document.getElementById("trebleInfo").innerText = 'TREB: ' + status_decode(status, 'treble');

    // MONO, LOUDNESS
        // Highlights activated buttons and related indicators
    if ( status_decode(status, 'muted') == 'true' ) {
        document.getElementById("buttonMute").style.background = "rgb(185, 185, 185)";
        document.getElementById("buttonMute").style.color = "white";
        document.getElementById("buttonMute").style.fontWeight = "bolder";
        document.getElementById("levelInfo").style.color = "rgb(150, 90, 90)";
    } else {
        document.getElementById("buttonMute").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonMute").style.color = "lightgray";
        document.getElementById("buttonMute").style.fontWeight = "normal";
        document.getElementById("levelInfo").style.color = "white";
    }
    if ( status_decode(status, 'midside') == 'mid' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'MO';
    } else if ( status_decode(status, 'midside') == 'side' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'L-R';
    } else {
        document.getElementById("buttonMono").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonMono").style.color = "white";
        document.getElementById("buttonMono").innerText = 'ST';
    }
    if ( status_decode(status, 'loudness_track') == 'true' ) {
        document.getElementById("buttonLoud").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonLoud").style.color = "white";
        document.getElementById("buttonLoud").innerText = 'LD';
    } else {
        document.getElementById("buttonLoud").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonLoud").style.color = "rgb(150, 150, 150)";
        document.getElementById("buttonLoud").innerText = 'LD';
    }

    // Loudspeaker name (can change in some systems)
    document.getElementById("main_center").innerText = ':: ' + get_loudspeaker_name() + ' ::';

}

// Getting files from server
function get_file(fid) {
    var phpCmd   = "";
    var response = "still_no_answer";
    if ( fid == 'config' ) {
        phpCmd = 'read_config_file';
    }
    else {
        return null;
    }
    var myREQ = new XMLHttpRequest();
    myREQ.open(method="GET", url="php/functions.php?command=" + phpCmd, async=false);
    myREQ.send();
    return (myREQ.responseText);
}

// Decodes the value from a pre.di.c parameter inside the pre.di.c status stream
function status_decode(status, prop) {
    var result = "";
    arr = status.split("\n"); // the tuples 'parameter:value' comes separated by line breaks
    for ( i in arr ) {
        if ( prop == arr[i].split(":")[0] ) {
            result = arr[i].split(":")[1]
        }
    }
    return String(result).trim();
}

// Gets the current loudspeaker name
function get_loudspeaker_name() {
    var myREQ = new XMLHttpRequest();
    myREQ.open(method="GET", url="php/functions.php?command=get_loudspeaker_name", async=false);
    myREQ.send();
    return (myREQ.responseText);
}

// Aux function that retrieves the indentation level of some code line, useful for YAML decoding.
function indentLevel(linea) {
    var level = 0;
    for ( i in linea ) {
        if ( linea[i] != ' ' ) { break;}
        level += 1;
    }
    return (level);
}

// Auxiliary to check for "numeric" strings
function isNumeric(num){
  return !isNaN(num)
}

// Auxiliary function to avoid http socket lossing some symbols
function http_prepare(x) {
    x = x.replace(' ', '%20')
    x = x.replace('!', '%21')
    x = x.replace('"', '%22')
    x = x.replace('#', '%23')
    x = x.replace('$', '%24')
    x = x.replace('%', '%25')
    x = x.replace('&', '%26')
    x = x.replace("'", '%27')
    x = x.replace('(', '%28')
    x = x.replace(')', '%29')
    x = x.replace('*', '%2A')
    x = x.replace('+', '%2B')
    x = x.replace(',', '%2C')
    x = x.replace('-', '%2D')
    x = x.replace('.', '%2E')
    x = x.replace('/', '%2F')
    return x;
}

// JUST TO TEST
function TESTING() {
    document.getElementById("loud_slider").value = 0;
}
