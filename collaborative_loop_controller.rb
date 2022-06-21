
# A very useful function provided by Robin Newman
define :parse_osc do | path |
  v = get_event(path).to_s.split(",")[6]
  if v != nil
    return v[3..-2].split("/")
  else
    return "Could not decipher osc path..."
  end
end

define :loopItem do | loop_hashes, key |
  my_list = get loop_hashes["lists"][key]
  next_idx = get loop_hashes["idx"][key]
  if next_idx > (my_list.length-1)
    next_idx = 0
  end
  my_item = my_list[next_idx]
  set loop_hashes["idx"][key], next_idx+1
  return my_item
end

use_osc "localhost", 12000

# heartbeat to show sonic pi is running
live_loop :heartbeat do
  osc "/sonicpi/im_here"
  sleep 1
end

define :effectMgr do | playDef, effects |
  # if effects length is zero, play sample using playDef
  if effects.length == 0
    print(playDef[:a])
    playSample playDef[:loopNum], playDef[:sam],playDef[:r],playDef[:a],playDef[:st],playDef[:fn]
  else
    # get next effect by getting item 0
    effectDef = effects.first
    # get a new effects list without the first element
    new_fx = effects[1,(effects.length-1)]
    # switch effect types and run effectMgr recursively with remaining effects
    case effectDef[:type]
    when 'echo'
      with_fx :echo, phase: effectDef[:phase], amp: playDef[:a] do
        effectMgr playDef, new_fx
      end
    when 'reverb'
      with_fx :reverb, room: effectDef[:room], amp: playDef[:a] do
        effectMgr playDef, new_fx
      end
    when 'lpf'
      with_fx :lpf, cutoff: effectDef[:cutoff], amp: playDef[:a] do
        effectMgr playDef, new_fx
      end
    when 'hpf'
      with_fx :hpf, cutoff: effectDef[:cutoff], amp: playDef[:a] do
        effectMgr playDef, new_fx
      end
    when 'distortion'
      with_fx :distortion, distort: effectDef[:distort], amp: playDef[:a] do
        effectMgr playDef, new_fx
      end
    else
      print("Unknown efffect type:")
      print(effectDef[:type])
    end
  end
end

# effects hash examples
#fx1 = {'type':'echo','phase':0.5}
#fx2 = {'type':'lpf','cutoff':30}
#fx3 = {'type':'distortion','distort':0.80}
#fx4 = {'type':'reverb','room':0.75}

define :playSample do |loopNum, sam,r,a,st,fn |
  osc "/sonicpi/playing", loopNum,st,r,fn,a
  sample sam,rate: r, amp: a, start: st, finish: fn
end

# Loop One Controls
l1_scalars = {
  'sample' => :sample1,
  'startPct' => :startPct1,
  'endPct' => :endPct1,
  'runPct' => :runPct1,
  'stepPct' => :stepPct1
}

l1_lists = {
  'sleep' => :sleeps1,
  'rate' => :rates1,
  'amp' => :amps1,
  'pan' => :pans1
}

l1_idx = {
  'sleep' => :sleepIdx1,
  'rate' => :rateIdx1,
  'amp' => :ampIdx1,
  'pan' => :panIdx1
}

l1_adv = 0

l1_scalars.each {|key, value| set l1_scalars[key],0  }
l1_lists.each {|key, value| set l1_lists[key],[1]  }
l1_idx.each {|key, value| set l1_idx[key],0  }

l1 = {
  'scalars' => l1_scalars,
  'lists' => l1_lists,
  'idx' => l1_idx
}

live_loop :loop1 do
  r = loopItem l1,'rate'
  next_slp = loopItem l1,'sleep'
  a = loopItem l1,'amp'
  stPct = get l1_scalars['startPct']
  stepPct = get l1_scalars['stepPct']
  endPct = get l1_scalars['endPct']
  runPct = get l1_scalars['runPct']
  st = stPct + l1_adv
  fn = st + runPct
  if fn > endPct
    l1_adv = 0
    st = stPct + l1_adv
    fn = st + runPct
  end
  puts "l1 rate: #{r}"
  puts "l1 amp: #{a}"
  puts "l1 stPct: #{stPct}"
  puts "l1 adv: #{l1_adv}"
  puts "l1 endPct: #{endPct}"
  puts "l1 runPct: #{runPct}"
  puts "l1 start: #{st}"
  puts "l1 finish: #{fn}"
  s = playSample 1,get(:sample1), r, a, st, fn
  l1_adv = l1_adv + stepPct
  if (l1_adv + runPct) > endPct
    l1_adv = 0
  end
  set :s1,s
  sleep next_slp
end

# Loop Two Controls
l2_scalars = {
  'sample' => :sample2,
  'startPct' => :startPct2,
  'endPct' => :endPct2,
  'runPct' => :runPct2,
  'stepPct' => :stepPct2
}

l2_lists = {
  'sleep' => :sleeps2,
  'rate' => :rates2,
  'amp' => :amps2,
  'pan' => :pans2
}

l2_idx = {
  'sleep' => :sleepIdx2,
  'rate' => :rateIdx2,
  'amp' => :ampIdx2,
  'pan' => :panIdx2
}

l2_adv = 0

l2_scalars.each {|key, value| set l2_scalars[key],0  }
l2_lists.each {|key, value| set l2_lists[key],[1]  }
l2_idx.each {|key, value| set l2_idx[key],0  }

l2 = {
  'scalars' => l2_scalars,
  'lists' => l2_lists,
  'idx' => l2_idx
}

live_loop :loop2 do
  r = loopItem l2,'rate'
  next_slp = loopItem l2,'sleep'
  a = loopItem l2,'amp'
  stPct = get(:startPct2)
  stepPct = get(:stepPct2)
  endPct = get(:endPct2)
  runPct = get(:runPct2)
  st = stPct + l2_adv
  fn = st + runPct
  if fn > endPct
    l2_adv = 0
    st = stPct + l2_adv
    fn = st + runPct
  end
  s = playSample 2,get(:sample2), r, a, st, fn
  l2_adv = l2_adv + stepPct
  if (l2_adv + runPct) > endPct
    l2_adv = 0
  end
  set :s2,s
  sleep next_slp
end

# Loop Three Controls
l3_scalars = {
  'sample' => :sample3,
  'startPct' => :startPct3,
  'endPct' => :endPct3,
  'runPct' => :runPct3,
  'stepPct' => :stepPct3
}

l3_lists = {
  'sleep' => :sleeps3,
  'rate' => :rates3,
  'amp' => :amps3,
  'pan' => :pans3
}

l3_idx = {
  'sleep' => :sleepIdx3,
  'rate' => :rateIdx3,
  'amp' => :ampIdx3,
  'pan' => :panIdx3
}

l3_adv = 0

l3_scalars.each {|key, value| set l3_scalars[key],0  }
l3_lists.each {|key, value| set l3_lists[key],[1]  }
l3_idx.each {|key, value| set l3_idx[key],0  }

l3 = {
  'scalars' => l3_scalars,
  'lists' => l3_lists,
  'idx' => l3_idx
}

live_loop :loop3 do
  r = loopItem l3,'rate'
  next_slp = loopItem l3,'sleep'
  a = loopItem l3,'amp'
  stPct = get(:startPct3)
  stepPct = get(:stepPct3)
  endPct = get(:endPct3)
  runPct = get(:runPct3)
  st = stPct + l3_adv
  fn = st + runPct
  if fn > endPct
    l3_adv = 0
    st = stPct + l3_adv
    fn = st + runPct
  end
  s = playSample 3,get(:sample3), r, a, st, fn
  l3_adv = l3_adv + stepPct
  if (l3_adv + runPct) > endPct
    l3_adv = 0
  end
  set :s3,s
  sleep next_slp
end
# Loop Four Controls
l4_scalars = {
  'sample' => :sample4,
  'startPct' => :startPct4,
  'endPct' => :endPct4,
  'runPct' => :runPct4,
  'stepPct' => :stepPct4
}

l4_lists = {
  'sleep' => :sleeps4,
  'rate' => :rates4,
  'amp' => :amps4,
  'pan' => :pans4
}

l4_idx = {
  'sleep' => :sleepIdx4,
  'rate' => :rateIdx4,
  'amp' => :ampIdx4,
  'pan' => :panIdx4
}

l4_adv = 0

l4_scalars.each {|key, value| set l4_scalars[key],0  }
l4_lists.each {|key, value| set l4_lists[key],[1]  }
l4_idx.each {|key, value| set l4_idx[key],0  }

l4 = {
  'scalars' => l4_scalars,
  'lists' => l4_lists,
  'idx' => l4_idx
}

live_loop :loop4 do
  r = loopItem l4,'rate'
  next_slp = loopItem l4,'sleep'
  a = loopItem l4,'amp'
  stPct = get(:startPct4)
  stepPct = get(:stepPct4)
  endPct = get(:endPct4)
  runPct = get(:runPct4)
  st = stPct + l4_adv
  fn = st + runPct
  if fn > endPct
    l4_adv = 0
    st = stPct + l4_adv
    fn = st + runPct
  end
  s = playSample 4,get(:sample4), r, a, st, fn
  l4_adv = l4_adv + stepPct
  if (l4_adv + runPct) > endPct
    l4_adv = 0
  end
  set :s4,s
  sleep next_slp
end

live_loop :osc_listener do
  m  = "/osc*/**" # everything which comes in as osc ...
  data  = sync m
  seg   = parse_osc m
  puts "Seg contains these elements: #{seg}"
  if seg[1] == 'l1'
    if l1_scalars.has_key?(seg[2])
      set l1_scalars[seg[2]], data[0]
    end
    if l1_lists.has_key?(seg[2])
      puts "l1 #{seg[2]} data: #{data}"
      set l1_lists[seg[2]], data
    end
  end
  if seg[1] == 'l2'
    if l2_scalars.has_key?(seg[2])
      set l2_scalars[seg[2]], data[0]
    end
    if l2_lists.has_key?(seg[2])
      puts "l2 #{seg[2]} data: #{data}"
      set l2_lists[seg[2]], data
    end
  end
  if seg[1] == 'l3'
    if l3_scalars.has_key?(seg[2])
      set l3_scalars[seg[2]], data[0]
    end
    if l3_lists.has_key?(seg[2])
      puts "l3 #{seg[2]} data: #{data}"
      set l3_lists[seg[2]], data
    end
  end
  if seg[1] == 'l4'
    if l4_scalars.has_key?(seg[2])
      set l4_scalars[seg[2]], data[0]
    end
    if l4_lists.has_key?(seg[2])
      puts "l4 #{seg[2]} data: #{data}"
      set l4_lists[seg[2]], data
    end
  end
end