const mongoose = require('mongoose');
const dotenv = require('dotenv');
const connectDB = require('../config/db');
const User = require('../models/User');
const Income = require('../models/Income');
const Expense = require('../models/Expense');
const Budget = require('../models/Budget');
const Transaction = require('../models/Transaction');

dotenv.config();

const seedData = async () => {
  try {
    await connectDB();

    // Clear existing database
    console.log('Clearing database collections...');
    await User.deleteMany();
    await Income.deleteMany();
    await Expense.deleteMany();
    await Budget.deleteMany();
    await Transaction.deleteMany();

    console.log('Database cleared.');

    // Create test user
    console.log('Creating test user...');
    const user = await User.create({
      name: 'John Doe',
      email: 'test@example.com',
      password: 'password123', // Will be hashed by pre-save hook
      currency: 'USD',
      theme: 'dark'
    });
    console.log(`Test user created: ${user.email}`);

    // Helper to generate dates
    const getPastDate = (daysAgo) => {
      const date = new Date();
      date.setDate(date.getDate() - daysAgo);
      return date;
    };

    const getCurrentMonthString = () => {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      return `${year}-${month}`;
    };

    const getPreviousMonthString = () => {
      const now = new Date();
      now.setMonth(now.getMonth() - 1);
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      return `${year}-${month}`;
    };

    // Set Budgets
    console.log('Creating budgets...');
    const currentMonth = getCurrentMonthString();
    const previousMonth = getPreviousMonthString();

    await Budget.create([
      { user: user._id, monthlyBudget: 3000, month: currentMonth },
      { user: user._id, monthlyBudget: 2500, month: previousMonth }
    ]);

    // Seed Incomes
    console.log('Creating income entries...');
    const incomes = [
      { amount: 5000, source: 'Monthly Salary', date: getPastDate(2), notes: 'Regular monthly salary' },
      { amount: 850, source: 'Freelance Design', date: getPastDate(5), notes: 'Mobile app project' },
      { amount: 5000, source: 'Monthly Salary', date: getPastDate(32), notes: 'Previous month salary' }
    ];

    for (const inc of incomes) {
      const income = await Income.create({
        user: user._id,
        amount: inc.amount,
        source: inc.source,
        date: inc.date,
        notes: inc.notes
      });

      // Sync to transaction
      await Transaction.create({
        user: user._id,
        type: 'income',
        amount: inc.amount,
        categoryOrSource: inc.source,
        date: inc.date,
        description: inc.notes || 'Income entry',
        referenceId: income._id
      });
    }

    // Seed Expenses
    console.log('Creating expense entries...');
    const expenses = [
      { amount: 1500, category: 'Rent', date: getPastDate(10), description: 'Apartment Rent' },
      { amount: 250, category: 'Food', date: getPastDate(3), description: 'Weekly groceries' },
      { amount: 75, category: 'Shopping', date: getPastDate(1), description: 'Clothing purchase' },
      { amount: 45, category: 'Fuel', date: getPastDate(4), description: 'Gas station' },
      { amount: 120, category: 'Entertainment', date: getPastDate(8), description: 'Concert tickets' },
      { amount: 1500, category: 'Rent', date: getPastDate(35), description: 'Apartment Rent' },
      { amount: 320, category: 'Food', date: getPastDate(33), description: 'Grocery shopping' },
      { amount: 180, category: 'Healthcare', date: getPastDate(40), description: 'Doctor checkup' }
    ];

    for (const exp of expenses) {
      const expense = await Expense.create({
        user: user._id,
        amount: exp.amount,
        category: exp.category,
        date: exp.date,
        description: exp.description
      });

      // Sync to transaction
      await Transaction.create({
        user: user._id,
        type: 'expense',
        amount: exp.amount,
        categoryOrSource: exp.category,
        date: exp.date,
        description: exp.description || 'Expense entry',
        referenceId: expense._id
      });
    }

    console.log('Database seeding completed successfully!');
    process.exit(0);
  } catch (error) {
    console.error(`Error seeding database: ${error.message}`);
    process.exit(1);
  }
};

seedData();
