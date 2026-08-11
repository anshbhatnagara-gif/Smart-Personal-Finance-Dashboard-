import React from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const ChartCard = ({ title, type = 'trend', chartData }) => {
  
  // Color configuration mapping for category breakdown
  const categoryColors = {
    'Food': '#f59e0b',          // Amber
    'Shopping': '#ec4899',      // Pink
    'Travel': '#3b82f6',        // Blue
    'Fuel': '#8b5cf6',          // Purple
    'Education': '#06b6d4',     // Cyan
    'Healthcare': '#10b981',    // Green
    'Entertainment': '#ef4444', // Red
    'Bills': '#f97316',         // Orange
    'Rent': '#6366f1',          // Indigo
    'Others': '#64748b'         // Slate
  };

  const getDoughnutData = () => {
    const labels = chartData.map(item => item.category);
    const data = chartData.map(item => item.amount);
    const backgroundColor = chartData.map(item => categoryColors[item.category] || '#94a3b8');

    return {
      labels,
      datasets: [
        {
          data,
          backgroundColor,
          borderColor: 'var(--bg-secondary)',
          borderWidth: 2,
          hoverOffset: 4,
        },
      ],
    };
  };

  const getBarData = () => {
    const labels = chartData.map(item => {
      // Format YYYY-MM into short month name (e.g. Aug)
      const [year, monthNum] = item.month.split('-');
      const date = new Date(year, monthNum - 1, 1);
      return date.toLocaleDateString('en-US', { month: 'short' });
    });
    const incomeData = chartData.map(item => item.income);
    const expenseData = chartData.map(item => item.expense);

    return {
      labels,
      datasets: [
        {
          label: 'Income',
          data: incomeData,
          backgroundColor: '#10b981',
          borderRadius: 4,
        },
        {
          label: 'Expenses',
          data: expenseData,
          backgroundColor: '#f43f5e',
          borderRadius: 4,
        },
      ],
    };
  };

  // Common chart styles for Premium Dark dashboard theme
  const getChartOptions = () => {
    const isLightTheme = document.body.classList.contains('light-theme');
    const labelColor = isLightTheme ? '#475569' : '#94a3b8';
    const gridColor = isLightTheme ? 'rgba(15, 23, 42, 0.05)' : 'rgba(255, 255, 255, 0.05)';

    if (type === 'breakdown') {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: labelColor,
              font: {
                family: 'var(--font-sans)',
                size: 11
              },
              boxWidth: 10,
              padding: 10
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.raw;
                const formatted = new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                }).format(value);
                return ` ${context.label}: ${formatted}`;
              }
            }
          }
        }
      };
    }

    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: labelColor,
            font: {
              family: 'var(--font-sans)',
              weight: '500'
            },
            boxWidth: 12
          }
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const value = context.raw;
              const formatted = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
              }).format(value);
              return ` ${context.dataset.label}: ${formatted}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false,
          },
          ticks: {
            color: labelColor,
            font: {
              family: 'var(--font-sans)'
            }
          }
        },
        y: {
          grid: {
            color: gridColor,
          },
          ticks: {
            color: labelColor,
            font: {
              family: 'var(--font-sans)'
            },
            callback: (value) => `$${value}`
          }
        }
      }
    };
  };

  return (
    <div className="panel animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
      <h3 style={{
        fontSize: '0.95rem',
        fontWeight: 600,
        color: 'var(--text-primary)',
        fontFamily: 'var(--font-display)'
      }}>
        {title}
      </h3>
      <div style={{ position: 'relative', flex: 1, minHeight: '240px' }}>
        {type === 'breakdown' ? (
          <Doughnut data={getDoughnutData()} options={getChartOptions()} />
        ) : (
          <Bar data={getBarData()} options={getChartOptions()} />
        )}
      </div>
    </div>
  );
};

export default ChartCard;
