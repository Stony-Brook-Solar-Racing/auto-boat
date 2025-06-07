# R Script: Read CSV, compute rolling average, and plot

# 1. Install and load required package
if (!requireNamespace("zoo", quietly = TRUE)) {
  install.packages("zoo")
}
library(zoo)

# 2. Read the CSV file
#    Make sure "data.csv" is in your working directory, or provide the full path.
df <- read.csv("data.csv", stringsAsFactors = FALSE)

# 3. Rename columns for easier reference
#    The original CSV has columns named "x (minutes)" and "y (voltage)".
names(df) <- c("time_min", "voltage")

# 4. Choose a window size for the rolling average (e.g., 5 points)
window_size <- 5

# 5. Compute the centered rolling average of 'voltage'
#    'fill = NA' will pad the ends with NA where a full window cannot be formed.
df$MA <- rollmean(df$voltage,
                  k     = window_size,
                  align = "center",
                  fill  = NA)

# 6. Plot the raw data points and overlay the rolling average

# 6a) Plot raw voltage vs. elapsed time (in minutes)
plot(df$time_min,
     df$voltage,
     type  = "p",           # points
     pch   = 16,            # solid circle
     col   = "steelblue",
     xlab  = "Time (minutes since start)",
     ylab  = "Voltage (V)",
     main  = paste0("Voltage over Time with ", window_size, "-Point Rolling Average")
)

# 6b) Add the rolling-average curve
lines(df$time_min,
      df$MA,
      col = "firebrick",
      lwd = 2
)

# 6c) Add a legend
legend("topright",
       legend = c("Raw voltage", paste0(window_size, "-point MA (centered)")),
       col    = c("steelblue", "firebrick"),
       pch    = c(16, NA),
       lty    = c(NA, 1),
       lwd    = c(NA, 2),
       bty    = "n"
)

# 7. (Optional) Print the data frame to console for inspection
print(df)

