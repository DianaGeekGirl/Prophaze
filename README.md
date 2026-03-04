# Prophaze
InterviewR2

'''
/Prophaze
├── AWS_keypair/
│   └── k8s-key.pem
├── images/
│   ├── app-running-browser.png
│   ├── kubectl_get_nodes.png
│   └── kubectl-get-pods-services.png
├── Movie_Scraper/
│   ├── app.py
│   ├── Dockerfile
│   ├── k8s/
│   │   ├── deployment.yaml
│   │   ├── namespace.yaml
│   │   └── service.yaml
│   ├── README.md
│   ├── requirements.txt
│   ├── results/
│   ├── templates/
│   │   └── index.html
│   └── webkyte_automation.py
└── README.md      (top‑level repo README)
'''


**Simple steps to run your app every time:**

Step 1 — Go to AWS Console
https://console.aws.amazon.com
→ EC2 → Instances
→ Select your instance
→ Instance State → Start Instance
→ Wait 1-2 minutes

Step 2 — Get new IP
Click on your instance
Copy "Public IPv4 address"
(IP changes every restart!)

Step 3 — SSH into EC2
bashcd ~/Desktop/prophaze/AWS_keypair
ssh -i k8s-key.pem ubuntu@<NEW_IP>

Step 4 — Check everything is running
bashkubectl get nodes
# should show: Ready

kubectl get pods
# should show: Running

kubectl get services
# should show: 5000:30007/TCP

**Step 5 — Open in browser**

http://<NEW_IP>:30007

'''If pods are NOT running:
bashsudo systemctl restart containerd
sleep 20
sudo systemctl restart kubelet
sleep 30
kubectl get pods'''

**Read README.md – it contains all cluster setup, deployment, and access instructions.** - Movie_Scraper/README.md
**View the images** in the images folder for examples of:
kubectl get pods / get services output
Browser screenshot of the running app
