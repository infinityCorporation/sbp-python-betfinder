This readme describes the package:

    betFinderScript - Alpha V0.1

The goal of the script is to find betting lines with a positive expected value
across multiple sports and bet types. Once found the script aims to save the
data to a storage location for later access. This is a standalone script that
is meant to be called on a minute basis to keep up with changing data in the
sports betting world. The script analyzes the data based on accepted mathematical
functions for computations on odds prices in american form. Below are lists of
what the script supports, the api the data is called from, updates, required
packages, and tasks still to do.

The currently supported sports are:
 - NCAA Football
 - NCAA Basketball
 - NBA
 - NFL
The currently supported bet types are:
 - H2H
 - Spreads
 - Totals
The script accesses the endpoint host:

    api.the-odds-api.com

The script process runs as follows:
   1. Pull data from odds api
   2. Parse data into correct format
   3. Loop through all bets calculating EV
       - Different analysis is required for h2h,spreads and totals
           - If positive, add to a list
           - Else, do nothing
   4. Format the list into a form accessible later and
      parsable by the client
   5. Save the list with a distinct name to S3 storage
   6. Remember to check each specific error case and to
      create a rigid error handling system.

REQUIRED PACKAGES:
 - > Python 3.0
 - http (built-int)
 - http.client (built-int)
 - NumPy
 - json
 - MatPlotLib.pyplot (Testing)

UPDATES:
 - The program can now pull all supported sports and bet data from the odds
   api (host listed above).
 - The program can analyze the basics and report the expected value of the return
   of a betting line.
 - The program currently has production code such as the main loops and functions
   and testing code such as certain lists and graphing utilities.

ToDo:
 This program is now finding positive EV bets for NCAA Football and Basketball as well
 as for NBA and NFL games. The next step is to figure out specifically how to return and
 package all necessary data to get it into storage. After getting the data into storage it
 will need to be accesses by the client, this can be grabbed and sent with the go manager
 script.
 A method needs to be found for how to call the script from the go server. This will require
 information such as where to host the script (on the same server or different), what determines
 the frequency with which it is called, and how maintenance on the script can be done when in
 production.
 Consider how multiline bets may be added to this script. There is a possibility that they
 may require their own script to more accurately and efficiently analyze the data.

