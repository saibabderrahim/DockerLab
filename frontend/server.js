const express = require('express');
const axios = require('axios');
const os = require('os'); // Import OS to get container hostname
const app = express();

app.set('view engine', 'ejs');
app.use(express.urlencoded({ extended: true }));

const BACKEND_URL = 'http://backend:3000/api/banking/account';
const TRANSFER_URL = 'http://backend:3000/api/banking/transfer';

app.get('/', async (req, res) => {
    try {
        const response = await axios.get(BACKEND_URL);

        // This comes from the Backend's header (X-Backend-Id)
        const backendName = response.headers['x-backend-id'];

        // This is this specific Frontend's injected name
        const frontendName = process.env.REPLICA_NAME || os.hostname();

        res.render('index', {
            account: response.data,
            backendId: backendName,
            frontendId: frontendName
        });
    } catch (err) {
        res.status(500).send("Backend Unreachable");
    }
});
//app.get('/', async (req, res) => {
//    try {
//        const response = await axios.get(BACKEND_URL);
//        
//        // ID from the Backend (via custom header)
//        const backendId = response.headers['x-backend-id'];
//        
//        // ID of this current Frontend container
//        const frontendId = os.hostname(); 
//
//        res.render('index', { 
//            account: response.data, 
//            backendId: backendId,
//            frontendId: frontendId 
//        });
//    } catch (err) {
//        console.error(err);
//        res.status(500).send("Backend Unreachable");
//    }
//});

app.post('/deposit', async (req, res) => {
    try {
        await axios.post(TRANSFER_URL, {
            amount: req.body.amount,
            description: "Web Deposit"
        });
        res.redirect('/');
    } catch (err) {
        res.status(500).send("Transaction Failed");
    }
});

// Health Check Endpoint
app.get('/health', (req, res) => {
    res.status(200).send('OK');
});

// Slow endpoint to simulate long-lived connections
app.get('/slow', async (req, res) => {
    const frontendName = process.env.REPLICA_NAME || os.hostname();

    // Simulate heavy / slow processing
    await new Promise(resolve => setTimeout(resolve, 10000)); // 10 seconds

    res.send(`Slow response from frontend ${frontendName}\n`);
});
app.listen(8080, () => console.log('Frontend running on port 8080'));


