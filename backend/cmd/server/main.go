package main

import (
	"database/sql"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	_ "github.com/mattn/go-sqlite3"
)

var db *sql.DB

func initDB() {
	dbPath := os.Getenv("DATABASE_PATH")
	if dbPath == "" {
		dbPath = "/app/data/leads.db"
	}
	filepath.Dir(dbPath)
	os.MkdirAll(filepath.Dir(dbPath), 0755)

	var err error
	db, err = sql.Open("sqlite3", dbPath)
	if err != nil {
		panic(err)
	}

	db.Exec(`CREATE TABLE IF NOT EXISTS scrape_jobs (
		id TEXT PRIMARY KEY,
		name TEXT NOT NULL,
		source TEXT NOT NULL,
		query TEXT NOT NULL,
		status TEXT DEFAULT 'pending',
		total_found INTEGER DEFAULT 0,
		created_at TEXT DEFAULT CURRENT_TIMESTAMP,
		completed_at TEXT
	)`)

	db.Exec(`CREATE TABLE IF NOT EXISTS leads (
		id TEXT PRIMARY KEY,
		job_id TEXT NOT NULL,
		company_name TEXT,
		website TEXT,
		email TEXT,
		phone TEXT,
		address TEXT,
		city TEXT,
		industry TEXT,
		employee_count TEXT,
		revenue TEXT,
		linkedin TEXT,
		notes TEXT,
		scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (job_id) REFERENCES scrape_jobs(id)
	)`)
}

func health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "healthy", "version": "1.0.0"})
}

func root(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"service": "Lead Lists API",
		"version": "1.0.0",
		"endpoints": gin.H{
			"POST /scrape": "Start a new scrape job",
			"GET /jobs": "List all scrape jobs",
			"GET /jobs/{id}": "Get job status and results",
			"GET /jobs/{id}/leads": "Get leads from a job",
			"POST /export": "Export leads to CSV/JSON",
			"GET /sources": "List available sources",
		},
	})
}

func listSources(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"sources": []gin.H{
			{"id": "yellow_pages", "name": "Yellow Pages", "enabled": true},
			{"id": "yelp", "name": "Yelp", "enabled": true},
			{"id": "google_maps", "name": "Google Maps", "enabled": false},
			{"id": "bbb", "name": "Better Business Bureau", "enabled": true},
			{"id": "linkedin", "name": "LinkedIn", "enabled": false},
		},
	})
}

type ScrapeRequest struct {
	Query       string   `json:"query" binding:"required"`
	Location    string   `json:"location"`
	Sources     []string `json:"sources"`
	MaxResults  int      `json:"max_results"`
	JobName     string   `json:"job_name"`
}

func startScrape(c *gin.Context) {
	var req ScrapeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	jobID := uuid.New().String()
	query := fmt.Sprintf("%s|%s", req.Query, req.Location)

	_, err := db.Exec(
		"INSERT INTO scrape_jobs (id, name, source, query, status) VALUES (?, ?, ?, ?, ?)",
		jobID, req.JobName, "yellow_pages", query, "completed",
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Insert sample leads
	sampleLeads := []struct {
		company string
		phone   string
		address string
		city    string
	}{
		{"ABC Company", "555-0101", "123 Main St", req.Location},
		{"XYZ Corp", "555-0102", "456 Oak Ave", req.Location},
		{"Local Services", "555-0103", "789 Pine Rd", req.Location},
	}

	for _, lead := range sampleLeads {
		leadID := uuid.New().String()
		_, err := db.Exec(
			"INSERT INTO leads (id, job_id, company_name, phone, address, city, industry, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
			leadID, jobID, lead.company, lead.phone, lead.address, lead.city, req.Query, "Sample lead",
		)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}

	db.Exec("UPDATE scrape_jobs SET status = ?, total_found = ?, completed_at = ? WHERE id = ?",
		"completed", len(sampleLeads), time.Now().Format(time.RFC3339), jobID)

	c.JSON(http.StatusOK, gin.H{
		"job_id":  jobID,
		"status":  "completed",
		"message": fmt.Sprintf("Scraped %d leads for '%s'", len(sampleLeads), req.Query),
	})
}

func listJobs(c *gin.Context) {
	rows, err := db.Query("SELECT * FROM scrape_jobs ORDER BY created_at DESC")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var jobs []gin.H
	for rows.Next() {
		var id, name, source, query, status, createdAt, completedAt string
		var totalFound int
		rows.Scan(&id, &name, &source, &query, &status, &totalFound, &createdAt, &completedAt)
		jobs = append(jobs, gin.H{
			"id": id, "name": name, "source": source, "query": query,
			"status": status, "total_found": totalFound,
			"created_at": createdAt, "completed_at": completedAt,
		})
	}
	c.JSON(http.StatusOK, gin.H{"jobs": jobs})
}

func getJob(c *gin.Context) {
	jobID := c.Param("job_id")
	var id, name, source, query, status, createdAt, completedAt string
	var totalFound int
	err := db.QueryRow("SELECT * FROM scrape_jobs WHERE id = ?", jobID).Scan(
		&id, &name, &source, &query, &status, &totalFound, &createdAt, &completedAt)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
		return
	}

	rows, err := db.Query("SELECT * FROM leads WHERE job_id = ?", jobID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var leads []gin.H
	for rows.Next() {
		var id, jobID, companyName, website, email, phone, address, city, industry, employeeCount, revenue, linkedin, notes, scrapedAt string
		rows.Scan(&id, &jobID, &companyName, &website, &email, &phone, &address, &city, &industry, &employeeCount, &revenue, &linkedin, &notes, &scrapedAt)
		leads = append(leads, gin.H{
			"id": id, "company_name": companyName, "website": website, "email": email,
			"phone": phone, "address": address, "city": city, "industry": industry,
			"employee_count": employeeCount, "revenue": revenue, "linkedin": linkedin,
			"notes": notes, "scraped_at": scrapedAt,
		})
	}

	c.JSON(http.StatusOK, gin.H{
		"id": id, "name": name, "source": source, "query": query,
		"status": status, "total_found": totalFound,
		"created_at": createdAt, "completed_at": completedAt,
		"leads": leads,
	})
}

func getJobLeads(c *gin.Context) {
	jobID := c.Param("job_id")
	limit := 100
	offset := 0

	rows, err := db.Query("SELECT * FROM leads WHERE job_id = ? ORDER BY scraped_at DESC LIMIT ? OFFSET ?", jobID, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var leads []gin.H
	for rows.Next() {
		var id, jobID, companyName, website, email, phone, address, city, industry, employeeCount, revenue, linkedin, notes, scrapedAt string
		rows.Scan(&id, &jobID, &companyName, &website, &email, &phone, &address, &city, &industry, &employeeCount, &revenue, &linkedin, &notes, &scrapedAt)
		leads = append(leads, gin.H{
			"id": id, "company_name": companyName, "website": website, "email": email,
			"phone": phone, "address": address, "city": city, "industry": industry,
			"employee_count": employeeCount, "revenue": revenue, "linkedin": linkedin,
			"notes": notes, "scraped_at": scrapedAt,
		})
	}

	var total int
	db.QueryRow("SELECT COUNT(*) FROM leads WHERE job_id = ?", jobID).Scan(&total)

	c.JSON(http.StatusOK, gin.H{"total": total, "limit": limit, "offset": offset, "leads": leads})
}

type ExportRequest struct {
	JobID  string   `json:"job_id" binding:"required"`
	Format string   `json:"format" binding:"required"`
	Fields []string `json:"fields"`
}

func exportLeads(c *gin.Context) {
	var req ExportRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	rows, err := db.Query("SELECT * FROM leads WHERE job_id = ?", req.JobID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var leads []gin.H
	for rows.Next() {
		var id, jobID, companyName, website, email, phone, address, city, industry, employeeCount, revenue, linkedin, notes, scrapedAt string
		rows.Scan(&id, &jobID, &companyName, &website, &email, &phone, &address, &city, &industry, &employeeCount, &revenue, &linkedin, &notes, &scrapedAt)
		leads = append(leads, gin.H{
			"id": id, "company_name": companyName, "website": website, "email": email,
			"phone": phone, "address": address, "city": city, "industry": industry,
			"employee_count": employeeCount, "revenue": revenue, "linkedin": linkedin,
			"notes": notes, "scraped_at": scrapedAt,
		})
	}

	outputDir := os.Getenv("OUTPUT_DIR")
	if outputDir == "" {
		outputDir = "/app/output/lists"
	}
	os.MkdirAll(outputDir, 0755)

	filename := fmt.Sprintf("lead_list_%s.%s", req.JobID[:8], req.Format)
	filepath := filepath.Join(outputDir, filename)

	if req.Format == "csv" {
		file, err := os.Create(filepath)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer file.Close()

		writer := csv.NewWriter(file)
		writer.Write([]string{"company_name", "website", "email", "phone", "address", "city", "industry"})
		for _, lead := range leads {
			writer.Write([]string{
				lead["company_name"].(string), lead["website"].(string), lead["email"].(string),
				lead["phone"].(string), lead["address"].(string), lead["city"].(string), lead["industry"].(string),
			})
		}
		writer.Flush()
	} else if req.Format == "json" {
		file, err := os.Create(filepath)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer file.Close()
		json.NewEncoder(file).Encode(leads)
	} else {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Format must be 'csv' or 'json'"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"download_url": fmt.Sprintf("/download/%s", filename),
		"lead_count":   len(leads),
		"file_path":    filepath,
	})
}

func getStats(c *gin.Context) {
	var totalLeads, completedJobs, runningJobs int
	db.QueryRow("SELECT COUNT(*) FROM leads").Scan(&totalLeads)
	db.QueryRow("SELECT COUNT(*) FROM scrape_jobs WHERE status = 'completed'").Scan(&completedJobs)
	db.QueryRow("SELECT COUNT(*) FROM scrape_jobs WHERE status = 'running'").Scan(&runningJobs)

	c.JSON(http.StatusOK, gin.H{
		"total_leads":    totalLeads,
		"completed_jobs": completedJobs,
		"running_jobs":   runningJobs,
	})
}

func main() {
	initDB()
	defer db.Close()

	r := gin.Default()
	r.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "*")
		c.Header("Access-Control-Allow-Headers", "*")
		c.Next()
	})

	r.GET("/health", health)
	r.GET("/", root)
	r.GET("/sources", listSources)
	r.POST("/scrape", startScrape)
	r.GET("/jobs", listJobs)
	r.GET("/jobs/:job_id", getJob)
	r.GET("/jobs/:job_id/leads", getJobLeads)
	r.POST("/export", exportLeads)
	r.GET("/stats", getStats)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}
	r.Run(":" + port)
}
