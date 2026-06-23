A small flask project which allows you to download the album covers of the saved albums which you have listened to (with a one song buffer), and then remove them from your library.  
Requires uploading of spotify data (as most data is not exposed by api) which can be found at https://www.spotify.com/us/account/privacy/ under "Extended Streaming History."  
Utilizes a small redis server for caching (not forcing to reupload everytime) and the spotify api.  
Has docker container setup included. To run, use  
```docker compose up```  
in the main directory, and then visit localhost:5000
