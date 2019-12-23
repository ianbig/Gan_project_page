var arrFilepath = [];


function showImg() {
    const url = 'http://localhost:2025/file';
    fetch(url,{
        method: 'GET',
        'content-type': 'application/json'
})
        .then((respone) => respone.json())
        .then((jsonData) => getImage(jsonData))
        .catch((err) => console.log(err));
}

function getImage(jsonData) {
    const container = document.getElementById('container');
    let id = 0;

    jsonData.forEach((imgPath) =>{
        const bottom = document.createElement('button');
        const path = '/data/' + imgPath;
        const box = document.createElement('img'); 
        bottom.setAttribute('class', 'imgClick');    
        bottom.setAttribute('id', id);   
        bottom.setAttribute('onclick', 'imgChoose(this.id)');
        box.setAttribute('class', 'img');
        box.setAttribute('src', path);
        bottom.appendChild(box);
        container.appendChild(bottom);
        id++;
    });
}

window.onload = function () {
    showImg();
}

function imgChoose(id) {
    "use strict";
    const imgChange = document.getElementById(id);
    const child = imgChange.firstChild;
    let path;
    if(child.nodeName == 'IMG') {
        path = child.src;
    }
    if(imgChange.style.borderColor == 'purple') {
        let index = arrFilepath.indexOf(path);
        if(index > -1) {
            arrFilepath.splice(index, 1); // syntax: splice(start, deleted index, things to insert)
        }
        imgChange.style.borderColor = 'white';
    }
    else {
        imgChange.style.borderColor = 'purple';
        arrFilepath.push(path);
    }
    //console.log(arrFilepath);
    
}

function sendData() {
    if(arrFilepath.length != 2) {
        // err handler
        console.log("error: phot not choose 2");
    }
    else {
        const mydata = JSON.stringify(arrFilepath);
        console.log(mydata);
        const url = 'http://localhost:2025/model';
        fetch(url, {
            method: 'POST',
            body: mydata,
            headers: {"Content-type": "application/json"}
        })
        .then((response) => console.log(response));
    }
}