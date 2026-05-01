create table if not exists public.usage_limits (
  identity_type text not null check (identity_type in ('anon', 'user')),
  identity_key text not null,
  window_start date not null,
  usage_count integer not null default 0,
  updated_at timestamptz not null default timezone('utc', now()),
  primary key (identity_type, identity_key, window_start)
);

create or replace function public.check_and_increment_usage_limit(
  p_identity_type text,
  p_identity_key text,
  p_daily_limit integer
)
returns table (
  allowed boolean,
  limit_value integer,
  remaining integer,
  reset_at timestamptz,
  current_count integer
)

language plpgsql
security definer
as $$
declare
  v_window_start date := timezone('utc', now())::date;
  v_count integer;
begin
  if p_daily_limit <= 0 then
    raise exception 'p_daily_limit must be > 0';
  end if;

  insert into public.usage_limits (identity_type, identity_key, window_start, usage_count)
  values (p_identity_type, p_identity_key, v_window_start, 1)
  on conflict (identity_type, identity_key, window_start)
  do update
    set usage_count = public.usage_limits.usage_count + 1,
    updated_at = timezone('utc', now())
  returning usage_count into v_count;

  return query
  select
    (v_count <= p_daily_limit) as allowed,
    p_daily_limit as limit_value,
    greatest(p_daily_limit - v_count, 0) as remaining,
    (v_window_start + interval '1 day')::timestamptz as reset_at,
    v_count as current_count;
end;
$$;

grant execute on function public.check_and_increment_usage_limit(text, text, integer) to anon;
grant execute on function public.check_and_increment_usage_limit(text, text, integer) to authenticated;
grant execute on function public.check_and_increment_usage_limit(text, text, integer) to service_role;
