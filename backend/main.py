"""
Harmony Concatenator - FastAPI Backend
"""
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yaml

from processor import HarmonyProcessor

app = FastAPI(title="Harmony Concatenator API")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active jobs
jobs = {}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/process")
async def process_data(
    config: UploadFile = File(...),
    data_zip: UploadFile = File(...)
):
    """
    Process uploaded Harmony data.
    
    Args:
        config: YAML configuration file
        data_zip: ZIP file containing plate folders
        
    Returns:
        Processing results and download URL
    """
    # Create temp directory for this job
    temp_dir = tempfile.mkdtemp(prefix="harmony_")
    
    try:
        # Save config file
        config_path = os.path.join(temp_dir, "config.yml")
        with open(config_path, "wb") as f:
            content = await config.read()
            f.write(content)
        
        # Validate config
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            required_fields = ['plate_format', 'plates', 'input_files']
            for field in required_fields:
                if field not in config_data:
                    raise HTTPException(status_code=400, detail=f"Missing required config field: {field}")
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")
        
        # Save and extract zip file
        zip_path = os.path.join(temp_dir, "data.zip")
        with open(zip_path, "wb") as f:
            content = await data_zip.read()
            f.write(content)
        
        # Extract zip
        input_dir = os.path.join(temp_dir, "input")
        os.makedirs(input_dir)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(input_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file")
        
        # Handle case where zip contains a single root folder
        contents = os.listdir(input_dir)
        if len(contents) == 1 and os.path.isdir(os.path.join(input_dir, contents[0])):
            input_dir = os.path.join(input_dir, contents[0])
        
        # Create output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)
        
        # Process the data
        processor = HarmonyProcessor()
        result = processor.process(input_dir, output_dir, config_path)
        
        # Create output zip
        output_zip_path = os.path.join(temp_dir, "results.zip")
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in os.listdir(output_dir):
                file_path = os.path.join(output_dir, file)
                zipf.write(file_path, file)
        
        # Store job info for download
        job_id = os.path.basename(temp_dir)
        jobs[job_id] = {
            "temp_dir": temp_dir,
            "output_zip": output_zip_path,
            "result": result
        }
        
        return {
            "success": True,
            "job_id": job_id,
            "result": result
        }
        
    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{job_id}")
async def download_results(job_id: str):
    """Download processed results as ZIP"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    
    job = jobs[job_id]
    return FileResponse(
        job["output_zip"],
        media_type="application/zip",
        filename="harmony_concatenated_results.zip"
    )


@app.delete("/api/cleanup/{job_id}")
async def cleanup_job(job_id: str):
    """Clean up temporary files for a job"""
    if job_id in jobs:
        shutil.rmtree(jobs[job_id]["temp_dir"], ignore_errors=True)
        del jobs[job_id]
    return {"status": "cleaned"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
