// Runs once, on the first start of the MongoDB container (docker-entrypoint-initdb.d).
// Local-only dummy credentials. Least privilege: Spark writes, the dashboard only reads.
const db = db.getSiblingDB("invoices");

db.createUser({ user: "app", pwd: "app", roles: [{ role: "readWrite", db: "invoices" }] });
db.createUser({ user: "dashboard", pwd: "dashboard", roles: [{ role: "read", db: "invoices" }] });

// Validates the invoice header; items stay flexible (documents can grow new fields).
db.createCollection("invoices", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["InvoiceNo", "InvoiceDate", "items"],
      properties: {
        InvoiceNo: { bsonType: "string" },
        CustomerID: { bsonType: ["string", "null"] },
        Country: { bsonType: ["string", "null"] },
        InvoiceDate: { bsonType: "date" },
        items: { bsonType: "array" },
      },
    },
  },
});

// The dashboard's queries: invoices of a customer (newest first), and the customer list
db.invoices.createIndex({ CustomerID: 1, InvoiceDate: -1 });
db.invoices.createIndex({ Country: 1 });
