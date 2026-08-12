## Data Model

### Entities


#### User

- `id: uuid`
- `email: str`
- `tier: enum`
- `created_at: datetime`

#### Subscription

- `id: uuid`
- `user_id: uuid`
- `status: enum`
- `ends_at: datetime`

#### UsageEvent

- `id: uuid`
- `user_id: uuid`
- `command: str`
- `credits: int`

### Relationships


- User 1:N Subscription
- User 1:N UsageEvent
- Subscription 1:N Invoice

### ER Diagram (text)

```

  [User]
  [Subscription]
  [UsageEvent]
```
