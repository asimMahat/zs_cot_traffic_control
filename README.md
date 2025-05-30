```markdown
# Zero-Shot CoT Traffic Signal Control

## Setup
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Generating the network
Sumo network is generated from nodes and edges files:
```bash
netconvert -c intersection.netccfg
```

## Generating routes
```bash
python generate_routes.py
``` 

## Running the controller
1. Set your OpenAI API key: `export OPENAI_API_KEY=<your_key>`
2. Launch:
   ```bash
   python run_controller.py
   ```
```

---