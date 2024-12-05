#!/bin/sh

set -e

host="$1"
shift
cmd="$@"

until pg_isready -h "$host" -p 5432 > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

echo "PostgreSQL is up - executing command"
exec $cmd
