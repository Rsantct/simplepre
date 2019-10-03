<?php

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

    /*  This is the hidden server side php code.
        PHP will response to the client via the standard php output, for instance:
            echo $some_varible;
            echo "some_string";
            readfile("some_file_path");
    */

    /////////////////////////////////////////////////////////////////////    
    // GLOBAL VARIABLES:
    $HOME = get_home();
    $CFG_FOLDER = $HOME.'/simplepre/config';
    $LSPKNAME = get_config('loudspeaker_name');
    /////////////////////////////////////////////////////////////////////

    // use only to cmdline debugging
    //echo '---'.$HOME.'---';
    //echo '---'.$CFG_FOLDER.'---';
    //echo '---'.$LSPKNAME.'---';

    // Gets the base folder where php code and 'simplepre' are located
    function get_home() {
        $phpdir = getcwd();
        $pos = strpos($phpdir, 'simplepre');
        return substr($phpdir, 0, $pos-1 );
    }

    // Gets single line configured items from an 'xxxxx.yml' file
    function get_config($item) {
        // 'global' to have access to variables outside
        global $CFG_FOLDER;
        $tmp = "";
        $cfile = fopen( $CFG_FOLDER."/config.yml", "r" )
                  or die("Unable to open file!");
        while( !feof($cfile) ) {
            $linea = fgets($cfile);
            // Ignore yaml commented out lines
            if ( strpos($linea, '#') === false ) {
                if ( strpos( $linea, $item) !== false ) {
                    $tmp = str_replace( "\n", "", $linea);
                    $tmp = str_replace( $item, "", $tmp);
                    $tmp = str_replace( ":", "", $tmp);
                    $tmp = trim($tmp);
                }
            }
        }
        fclose($cfile);
        return $tmp;
    }

    // Communicates to the TCP/IP servers.
    // Notice: server address and port are specified
    //         into 'config.yml' for each service,
    //         for instance 'control'
    function simplepre_socket ($service, $cmd) {
    
        $address = get_config( $service."_addr" );
        $port    = intval( get_config( $service."_port" ) );
        
        // Creates a TCP socket
        $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
        if ($socket === false) {
            echo "socket_create() failed: " . socket_strerror(socket_last_error()) . "\n";
        }
        $result = socket_connect($socket, $address, $port);
        if ($result === false) {
            echo "socket_connect() failed: ($result) " . socket_strerror(socket_last_error($socket)) . "\n";
        }
        // Sends and receive:
        socket_write($socket, $cmd, strlen($cmd));
        $out = socket_read($socket, 4096);
        // Tells the server to close the connection from its end:
        socket_write($socket, "quit", strlen("quit"));
        // Empties the receiving buffer:
        socket_read($socket, 4096);
        // And close this end socket:
        socket_close($socket);
        return $out;
    }

    ///////////////////////////   MAIN: ///////////////////////////////
    // listen to http request then returns results via standard output

    /*  http://php.net/manual/en/reserved.variables.request.php
        PHP server side receives associative arrays, i.e. dictionaries, through by the 
        GET o PUT methods from the client side HTTPREQUEST (usually javascript).
        The array is what appears after 'php/functions.php?.......', example:
                "GET", "php/functions.php?command=level -15"
        Here the key 'command' has the value 'level -15'
        So, lets read the key 'command', then run corresponding actions:
    */
    $command = $_REQUEST["command"];

    // READING THE LOUDSPEAKER NAME:
    if ( $command == "get_loudspeaker_name" ) {
        echo get_config("loudspeaker_name");
    }

    // readfile() does an 'echo', so it returns the contents 
    // of a file to the standard php output
    elseif ( $command == "read_config_file" ) {
        readfile($CFG_FOLDER."/config.yml");
    }
    
    // CONTROL SERVICE: any else will be an STANDARD CONTROL command, handled by the 'control' server
    else {
        echo simplepre_socket( 'server', $command );
    }

?>
