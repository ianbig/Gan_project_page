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
		const newdir_src = '~/桌面/project/PairedCycleGAN-tf/data/web_src';
		const newdir_ref = '~/桌面/project/PairedCycleGAN-tf/data/web_ref'
		let oldpath = req.body[0].replace('http://localhost:2025/data','~/桌面/AI_project/public/data/');
		let newpath =newdir_src + oldpath.replace('~/桌面/AI_project/public/data/','');
		console.log(newpath);
		console.log(oldpath);
		//fs.rename(oldpath, newpath, (err) => console.log(err));
		oldpath = req.body[1].replace('http://localhost:2025/','~/桌面/AI_project/public/data/');
		newpath = newdir_ref + oldpath.replace('~/桌面/AI_project/public/data/','');
		//fs.rename(oldpath, newpath, (err) => console.log(err))
		
	});

	app.listen(2025, function() {
		console.log('server is running on port 2025');
	});
}

getNames();
