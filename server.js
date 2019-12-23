function getNames() {
	const dir = './public/data';
	const bodyParser = require('body-parser');
	const express = require('express');
	const app = express();

	app.use(express.static('public'));
	app.use(express.static('data'));
	app.use(bodyParser.json());

	app.get('/file', function(req, res) {
		const fs = require('fs');
		const fileNames = fs.readdirSync(dir);
		res.send(JSON.stringify(fileNames));
	});

	app.post('/model', function(req, res) {
		const fs = require('fs');
		const newdir_src = '~/桌面/project/PairedCycleGAN-tf/data/web_src/';
		const newdir_ref = '~/桌面/project/PairedCycleGAN-tf/data/web_ref/'
		let oldpath = req.body[0].replace('http://localhost:2025/data','~/桌面/AI_project/public/data');
		let newpath = newdir_src;
		let exec = require('child_process').exec;
		let execSync = require('child_process').execSync;
		let command = 'mv ' + oldpath + " " + newpath;

		initData();

		exec(command, (err) => {
			if(err != null) console.log(err);
		});
		oldpath = req.body[1].replace('http://localhost:2025/data','~/桌面/AI_project/public/data');
		newpath = newdir_ref;
		command = 'mv ' + oldpath + " " + newpath;

		execSync(command);
		execSync('conda activate py36tf');
		execSync('python ~/桌面/project/PairedCycleGAN-tf/train-test.py');
		console.log('model start creating');

		res.send('well done');
		
	});

	app.listen(2025, function() {
		console.log('server is running on port 2025');
	});
}

function initData() {
	const fs = require('fs');
	const refPath = '/home/tjc105u/桌面/project/PairedCycleGAN-tf/data/web_ref/';
	const srcPath = '/home/tjc105u/桌面/project/PairedCycleGAN-tf/data/web_src/';
	let dataSrc = fs.readdirSync(srcPath);
	let dataRef = fs.readdirSync(refPath);
	const execSync = require('child_process').execSync;
	const origPath = '~/桌面/AI_project/public/data/';
	let i, j;
	

	for(i = 0; i < dataSrc.length; i++) { 
		let command = 'mv ' + srcPath + dataSrc[i] + ' ' + origPath;
		//execSync(command);
		
	}

	for(j = 0; j< dataRef.length; j++) {
		let command = 'mv ' + refPath + dataRef[j] + ' ' + origPath;
		console.log(command);
		//execSync(command);
	}
}
//getNames();
initData();